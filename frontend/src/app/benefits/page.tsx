"use client";
import React, { useState, useEffect } from "react";

export default function BenefitsPage() {
  const [file, setFile] = useState<File | null>(null);
  const [files, setFiles] = useState<string[]>([]);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  
  // Add states for tracking upload progress
  const [uploadStatus, setUploadStatus] = useState<string>("");
  const [isUploading, setIsUploading] = useState(false);

  // Add loading state
  const [isAsking, setIsAsking] = useState(false);

  // Fetch list of files with embeddings
  const fetchFiles = async () => {
    const response = await fetch("http://localhost:8000/rag/list_files/");
    const data = await response.json();
    setFiles(data.map((file: any) => file.filename));
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  // Upload PDF
  const handleUpload = async () => {
    if (!file) return;
    
    setIsUploading(true);
    setUploadStatus("Checking database...");
    
    const formData = new FormData();
    formData.append("file", file);
    
    try {
      setUploadStatus("Checking if file already exists in Vector Store...");
      
      const response = await fetch("http://localhost:8000/rag/upload/", { 
        method: "POST", 
        body: formData 
      });
      
      const result = await response.json();
      
      if (response.ok) {
        setUploadStatus(result.message);
        // Refresh the file list after upload
        fetchFiles();
        // Clear the file input
        setFile(null);
      } else {
        setUploadStatus(`Error: ${result.detail || 'Upload failed'}`);
      }
      
    } catch (error) {
      setUploadStatus("Upload failed!");
      console.error("Upload error:", error);
    } finally {
      setIsUploading(false);
      // Remove the setTimeout - message will stay until next action
      // setTimeout(() => setUploadStatus(""), 3000);
    }
  };

  // Delete embeddings
  const handleDelete = async () => {
    if (!selectedFile) return;
    
    try {
      await fetch("http://localhost:8000/rag/delete_by_filename/", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: selectedFile }),
      });
      
      alert("Deleted!");
      
      // Refresh the file list after deletion
      fetchFiles();
      setSelectedFile(null);
      
    } catch (error) {
      alert("Delete failed!");
      console.error("Delete error:", error);
    }
  };

  // Ask a question
  const handleAsk = async () => {
    if (!question.trim()) return;
    
    setIsAsking(true);
    try {
      const res = await fetch("http://localhost:8000/rag/ask/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const data = await res.json();
      setAnswer(data.answer);
    } catch (error) {
      setAnswer("Error: Failed to get answer");
    } finally {
      setIsAsking(false);
    }
  };

  return (
    <div>
      <h2>Benefits</h2>
      <div style={{ marginBottom: '2rem' }} />
      
      <div style={{ marginBottom: "2rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "0.5rem" }}>
          <h3 style={{ margin: 0, fontWeight: "normal" }}>Upload a file to the Vector Store</h3>
          <input 
            type="file" 
            accept="application/pdf" 
            onChange={e => setFile(e.target.files?.[0] || null)} 
          />
        </div>
        <button 
          onClick={handleUpload} 
          disabled={isUploading || !file}
          style={{ 
            cursor: isUploading || !file ? 'not-allowed' : 'pointer',
            backgroundColor: isUploading || !file ? '#f0f0f0' : '#d9d9d9',
            color: isUploading || !file ? '#666' : 'black',
            border: '1px solid #ccc',
            padding: '0.2rem 0.5rem',
            borderRadius: '4px',
            fontSize: '1rem',
          }}
        >
          {isUploading ? "Uploading..." : "Upload PDF"}
        </button>
        
        {/* Status display */}
        {uploadStatus && (
          <div style={{ 
            marginTop: "1rem", 
            padding: "0.5rem", 
            borderRadius: "4px",
            backgroundColor: uploadStatus.includes("Error") ? "#ffebee" : "#e8f5e8",
            color: uploadStatus.includes("Error") ? "#c62828" : "#2e7d32",
            border: `1px solid ${uploadStatus.includes("Error") ? "#ffcdd2" : "#c8e6c9"}`
          }}>
            {uploadStatus}
          </div>
        )}
      </div>
      
      <div style={{ marginBottom: "2rem" }}>
        <h3 style={{ margin: 0, marginBottom: "0.5rem", fontWeight: "normal" }}>Files in the Vector Store:</h3>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem", alignItems: "center" }}>
          {files.length === 0 ? (
            <span style={{ color: "#666", fontStyle: "italic" }}>No files uploaded yet</span>
          ) : (
            files.map(f => (
              <div key={f} style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <input 
                  type="radio" 
                  name="file" 
                  value={f} 
                  onChange={() => setSelectedFile(f)} 
                />
                <span>{f}</span>
              </div>
            ))
          )}
        </div>
        <button 
          onClick={handleDelete} 
          disabled={!selectedFile}
          style={{ 
            marginTop: "0.5rem",
            backgroundColor: !selectedFile ? '#f0f0f0' : '#d9d9d9',
            color: !selectedFile ? '#666' : 'black',
            border: '1px solid #ccc',
            padding: '0.2rem 0.5rem',
            borderRadius: '4px',
            fontSize: '1rem',
            cursor: !selectedFile ? 'not-allowed' : 'pointer'
          }}
        >
          Delete Selected File Embeddings
        </button>
      </div>
      
      <div style={{ marginTop: "3rem", marginBottom: "2rem" }}>
        <h3 style={{ margin: 0, marginBottom: "1rem", fontWeight: "normal" }}>Ask a question:</h3>
        <div style={{ display: "flex", alignItems: "flex-start", gap: "1rem" }}>
          <textarea 
            value={question} 
            onChange={e => setQuestion(e.target.value)}
            placeholder="Type your question here..."
            style={{
              flex: 0.5,
              minHeight: "30px",
              padding: "0.75rem",
              border: "1px solid #ccc",
              borderRadius: "4px",
              fontSize: "1rem",
              resize: "vertical",
              fontFamily: "inherit"
            }}
          />
          <button 
            onClick={handleAsk}
            disabled={isAsking || !question.trim()}
            style={{
              backgroundColor: isAsking || !question.trim() ? "#f0f0f0" : "#d9d9d9",
              color: isAsking || !question.trim() ? "#666" : "black",
              border: "1px solid #ccc",
              padding: "0.5rem 1rem",
              borderRadius: "4px",
              fontSize: "1rem",
              cursor: isAsking || !question.trim() ? "not-allowed" : "pointer",
              whiteSpace: "nowrap",
              alignSelf: "flex-start"
            }}
          >
            {isAsking ? "Asking..." : "Ask"}
          </button>
        </div>
      </div>
      
      {/* Show loading or answer */}
      {isAsking && (
        <div style={{ marginTop: "1rem" }}>
          <h3 style={{ fontWeight: "normal" }}>Answer:</h3>
          <div>Loading...</div>
        </div>
      )}

      {answer && !isAsking && (
        <div>
          <h3 style={{ fontWeight: "normal" }}>Answer:</h3>
          <div>{answer}</div>
        </div>
      )}
    </div>
  );
}