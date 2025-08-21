"use client";
import React, { useState } from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { format } from "date-fns";

export default function EvaluateMoodsSymptomsPage() {
  const [startDate, setStartDate] = useState<Date | null>(new Date());
  const [endDate, setEndDate] = useState<Date | null>(new Date());
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleEvaluate = async () => {
    if (!startDate || !endDate) {
      setResult("Please select a valid date range.");
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const response = await fetch("/api/evaluate/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          start_date: format(startDate, "yyyy-MM-dd"),
          end_date: format(endDate, "yyyy-MM-dd"),
        }),
      });
      if (!response.ok) {
        throw new Error("Failed to fetch evaluation.");
      }
      const data = await response.json();
      setResult(data.summary || "No summary available.");
    } catch (error) {
      setResult("Error: " + (error as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>Evaluate moods & symptoms</h1>
      <div style={{ margin: "2rem 0", display: "flex", alignItems: "center", gap: "0.5rem" }}>
        <label>Start Date:</label>
        <DatePicker
          selected={startDate ?? undefined}
          onChange={(date) => setStartDate(date)}
          selectsStart
          startDate={startDate ?? undefined}
          endDate={endDate ?? undefined}
          dateFormat="yyyy-MM-dd"
          placeholderText="Select start date"
        />
        <label>End Date:</label>
        <DatePicker
          selected={endDate ?? undefined}
          onChange={(date) => setEndDate(date)}
          selectsEnd
          startDate={startDate ?? undefined}
          endDate={endDate ?? undefined}
          minDate={startDate ?? undefined}
          dateFormat="yyyy-MM-dd"
          placeholderText="Select end date"
        />
        <button
          onClick={handleEvaluate}
          style={{
            padding: "0.3rem 0.8rem",
            background: "#666666",
            color: "#fff",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
            fontSize: "0.9rem"
          }}
          disabled={loading}
        >
          {loading ? "Evaluating..." : "Evaluate"}
        </button>
      </div>
      <div
        style={{
          minHeight: "100px",
          background: "#f4f4f4",
          borderRadius: "8px",
          padding: "1rem",
          marginTop: "1rem"
        }}
      >
        {result ? <p>{result}</p> : <p>No evaluation yet.</p>}
      </div>
    </div>
  );
}