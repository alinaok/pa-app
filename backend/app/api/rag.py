import os
from fastapi import APIRouter, UploadFile, File, Body, Form, HTTPException
from app.ai.rag import ingest_pdfs, graph, delete_embeddings_by_filename, index
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import Depends
from app.db.session import get_db
from app.models.rag import EmbeddedFile
from app.schemas.rag import EmbeddedFileOut


folder_path = os.path.join(os.path.dirname(__file__), "../ai/pdfs")
folder_path = os.path.abspath(folder_path)
os.makedirs(folder_path, exist_ok=True)  # Ensure the folder exists

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/upload/")
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # 1. Check if file is already embedded in DB first
    existing = db.query(EmbeddedFile).filter_by(filename=file.filename).first()
    if existing:
        return {"message": f"File {file.filename} is already in Vector Store"}
    
    # 2. If file name is not in DB, add it to embedded_files table first
    new_file = EmbeddedFile(filename=file.filename)
    db.add(new_file)
    db.commit()
    
    try:
        # 3. Save file to disk
        file_location = f"{folder_path}/{file.filename}"
        file_content = await file.read()  # Read content once
        with open(file_location, "wb") as f:
            f.write(file_content)
        
        # 4. Ingest and embed into Pinecone
        num_new_embeddings, newly_added_files = ingest_pdfs(filenames=[file.filename])
        
        return {"message": f"Added file {file.filename} to Vector Store"}
    
    except Exception as e:
        # If something goes wrong, remove the DB entry
        db.delete(new_file)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

@router.post("/ingest/")
async def ingest_endpoint(filenames: Optional[List[str]] = Form(None)):
    num_new_embeddings, newly_added_files = ingest_pdfs(filenames=filenames)
    return {
        "status": "PDFs ingested",
        "new_embeddings_added": num_new_embeddings,
        "newly_added_files": newly_added_files
    }

@router.delete("/delete_by_filename/")
async def delete_by_filename(filename: str = Body(..., embed=True), db: Session = Depends(get_db)):
    # Delete embeddings from Pinecone
    result = delete_embeddings_by_filename(filename)
    # Delete the record from the "embedded_files" table
    db.query(EmbeddedFile).filter_by(filename=filename).delete()
    db.commit()
    return {"status": "deleted", "filename": filename, "result": result}

@router.post("/ask/")
async def ask_endpoint(question: str = Body(..., embed=True)):
    response = graph.invoke({"question": question})
    return {"answer": response["answer"]}

@router.get("/list_files/", response_model=List[EmbeddedFileOut])
async def list_files(db: Session = Depends(get_db)):
    return db.query(EmbeddedFile).all()