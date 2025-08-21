import os
import getpass
from typing import Optional, List
from typing_extensions import TypedDict
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain.prompts import ChatPromptTemplate
from pinecone import Pinecone, ServerlessSpec
from langgraph.graph import START, StateGraph


# === Load API Keys ===
if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter OpenAI API key: ")

if not os.environ.get("PINECONE_API_KEY"):
    os.environ["PINECONE_API_KEY"] = getpass.getpass("Enter Pinecone API key: ")

# === Constants ===
folder_path = os.path.join(os.path.dirname(__file__), "pdfs")
index_name = "benefits-embeddings"
embedding_dim = 1536
batch_size = 100

# === Initialize Pinecone and Index ===
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])

if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=embedding_dim,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )

index = pc.Index(index_name)

# === LLM & Embeddings ===
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
vector_store = PineconeVectorStore(embedding=embedding_model, index=index)

# === Ingest Pipeline ===
def ingest_pdfs(filenames: Optional[List[str]] = None):
    print("Ingesting PDFs...")
    all_docs = []
    file_to_new_chunk = {}

    files_to_process = filenames or [f for f in os.listdir(folder_path) if f.endswith(".pdf")]
    # If filenames is given → process only those.
    # If filenames is None → process all .pdf files in pdfs/ folder.

    for filename in files_to_process:
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(folder_path, filename)
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            all_docs.extend(docs)

    splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=300)
    chunks = splitter.split_documents(all_docs)

    # Generate deterministic, file-specific IDs for chunks
    from collections import defaultdict
    chunk_counters = defaultdict(int)
    unique_ids = []
    for chunk in chunks:
        filename = os.path.basename(chunk.metadata.get("source", "unknown.pdf"))
        page = chunk.metadata.get("page", -1)
        idx = chunk_counters[(filename, page)]
        unique_ids.append(f"{filename}-page-{page}-chunk-{idx}")
        chunk_counters[(filename, page)] += 1

    existing_ids = set()
    for i in range(0, len(unique_ids), batch_size):
        batch_ids = unique_ids[i:i + batch_size]
        result = index.fetch(ids=batch_ids)
        existing_ids.update(result.vectors.keys())
        # Skips chunks whose IDs already exist in the Pinecone vector index.

    filtered_chunks = []
    filtered_ids = []
    for chunk, uid in zip(chunks, unique_ids):
        if uid not in existing_ids:
            filtered_chunks.append(chunk)
            filtered_ids.append(uid)
            filename = os.path.basename(chunk.metadata.get("source", "unknown.pdf"))
            file_to_new_chunk[filename] = file_to_new_chunk.get(filename, 0) + 1
            # Tracks new chunks and which files contributed them.

    print(f"New chunks to embed: {len(filtered_chunks)}")

    chunk_texts = [chunk.page_content for chunk in filtered_chunks]
    embeddings = embedding_model.embed_documents(chunk_texts)

    to_upsert = []
    for uid, chunk, vector in zip(filtered_ids, filtered_chunks, embeddings):
        metadata = chunk.metadata
        source_file = os.path.basename(metadata.get("source", "unknown.pdf"))
        page_label = metadata.get("page_label") or str((metadata.get("page") or -1) + 1)

        to_upsert.append((
            uid, vector, {
                "text": chunk.page_content,
                "filename": source_file,
                "page_label": page_label,
            }
        ))

    for i in range(0, len(to_upsert), batch_size):
        batch = to_upsert[i:i + batch_size]
        index.upsert(vectors=batch)

    newly_added_files = [fname for fname, count in file_to_new_chunk.items() if count > 0]
    print(f"PDF Ingest complete. {len(newly_added_files)} files added to Pinecone.")
    return len(filtered_chunks), newly_added_files

def delete_embeddings_by_filename(filename: str):
    # Connect to your index
    # (Assume `index` is already initialized as in your code)
    # Delete all vectors where metadata 'filename' matches
    delete_response = index.delete(
        filter={"filename": {"$eq": filename}}
    )
    print(f"Deleted all vectors for file: {filename}")
    return delete_response

# === Prompt Template ===
prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a helpful assistant that answers strictly from the provided context. "
     "If the answer is not in the context, say \"The information is not available in the provided documents.\""),
    ("human",
     "Context:\n{context}\n\n"
     "Question: {question}\n\n"
     "Answer in markdown:")
])

# === Retrieval + Generation Graph ===
class State(TypedDict):
    question: str
    context: List[Document]
    answer: str

def retrieve(state: State):
    docs = vector_store.similarity_search(state["question"], k=5)
    return {"context": docs}

def generate(state: State):
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    messages = prompt.invoke({"question": state["question"], "context": docs_content})
    response = llm.invoke(messages)
    return {"answer": response.content}

graph_builder = StateGraph(State).add_sequence([retrieve, generate])
graph_builder.add_edge(START, "retrieve")
graph = graph_builder.compile()

# === CLI Entry Point ===
def main():
    while True:
        print("\nWhat would you like to do?")
        print("1. Ingest PDFs")
        print("2. Ask a question")
        print("3. Exit")
        choice = input("Choose an option (1/2/3): ").strip()

        if choice == "1":
            ingest_pdfs()
        elif choice == "2":
            user_question = input("Enter your question: ")
            response = graph.invoke({"question": user_question})
            print("\nAnswer:")
            print(response["answer"])
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main()



# PDF Ingestion - Loads, chunks, filters, embeds. 
# Deduplication - Skips already embedded chunks
# Vector Indexing - Stores vectors in Pinecone
# Retrieval & Answering - Uses LangGraph for semantic QA
# LLM Answer Generation - GPT-4o-mini using retrieved context
