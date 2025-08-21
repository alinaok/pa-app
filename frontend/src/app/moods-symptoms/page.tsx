"use client";
import { useRouter } from "next/navigation";

export default function MoodsSymptomsPage() {
  const router = useRouter();

  return (
    <div style={{ padding: "0rem 2rem 2rem 1rem" }}>
      <h1 style={{ marginTop: 0, marginBottom: "2rem" }}>Moods & Symptoms</h1>
      <div
        onClick={() => router.push("/moods-symptoms/log")}
        style={{
          cursor: "pointer",
          padding: "1rem",
          fontSize: "1.2rem",
          background: "#f5f5fa",
          borderRadius: 6,
          marginBottom: "1rem",
          transition: "background 0.2s",
        }}
        onMouseOver={e => (e.currentTarget.style.background = "#e0e0eb")}
        onMouseOut={e => (e.currentTarget.style.background = "#f5f5fa")}
      >
        Log mood/symptom
      </div>
      <div
        onClick={() => router.push("/moods-symptoms/evaluate")}
        style={{
          cursor: "pointer",
          padding: "1rem",
          fontSize: "1.2rem",
          background: "#f5f5fa",
          borderRadius: 6,
          transition: "background 0.2s",
        }}
        onMouseOver={e => (e.currentTarget.style.background = "#e0e0eb")}
        onMouseOut={e => (e.currentTarget.style.background = "#f5f5fa")}
      >
        Evaluate
      </div>
    </div>
  );
}
