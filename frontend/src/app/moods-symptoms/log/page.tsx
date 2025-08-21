"use client";
import React, { useState } from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { useAuth } from "@/context/AuthContext";
import { FaTrash } from "react-icons/fa"; // Add this import

type MoodLog = {
  id: string;
  mood_type?: string;
  description: string;
  intensity?: number;
  created_at: string;
};

type SymptomLog = {
  id: string;
  description: string;
  created_at: string;
};

export default function LogMoodSymptomPage() {
  const { token } = useAuth();
  const [mood, setMood] = useState("");
  const [moodDescription, setMoodDescription] = useState("");
  const [moodIntensity, setMoodIntensity] = useState<number | "">("");
  const [symptom, setSymptom] = useState("");
  const [moodDate, setMoodDate] = useState<Date | null>(null);
  const [symptomDate, setSymptomDate] = useState<Date | null>(null);
  const [advice, setAdvice] = useState<string | null>(null);
  const [affirmation, setAffirmation] = useState<string | null>(null);
  const [pepTalk, setPepTalk] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isAdviceLoading, setIsAdviceLoading] = useState(false);

  // History states
  const [moodHistory, setMoodHistory] = useState<MoodLog[]>([]);
  const [symptomHistory, setSymptomHistory] = useState<SymptomLog[]>([]);
  const [moodHistoryFilter, setMoodHistoryFilter] = useState<'30days' | 'all' | null>(null);
  const [symptomHistoryFilter, setSymptomHistoryFilter] = useState<'30days' | 'all' | null>(null);
  const [isLoadingMoodHistory, setIsLoadingMoodHistory] = useState(false);
  const [isLoadingSymptomHistory, setIsLoadingSymptomHistory] = useState(false);

  // Add delete loading states
  const [deletingMoodId, setDeletingMoodId] = useState<string | null>(null);
  const [deletingSymptomId, setDeletingSymptomId] = useState<string | null>(null);

  const fetchAdvice = async (symptomDescription: string): Promise<string> => {
    const res = await fetch(`http://localhost:8000/symptoms/generate-advice?description=${encodeURIComponent(symptomDescription)}`);
    if (!res.ok) {
      throw new Error("Failed to fetch advice");
    }
    const data = await res.json();
    return data.advice;
  };

  // Fetch mood history
  const fetchMoodHistory = async (filter: '30days' | 'all') => {
    setIsLoadingMoodHistory(true);
    try {
      const token = localStorage.getItem("token");
      let url = "http://localhost:8000/moods";
      
      if (filter === '30days') {
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        url += `?start_date=${thirtyDaysAgo.toISOString().split('T')[0]}`;
      }
      
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setMoodHistory(data);
        setMoodHistoryFilter(filter);
      }
    } catch (error) {
      console.error("Error fetching mood history:", error);
    } finally {
      setIsLoadingMoodHistory(false);
    }
  };

  // Fetch symptom history
  const fetchSymptomHistory = async (filter: '30days' | 'all') => {
    setIsLoadingSymptomHistory(true);
    try {
      const token = localStorage.getItem("token");
      let url = "http://localhost:8000/symptoms";
      
      if (filter === '30days') {
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        url += `?start_date=${thirtyDaysAgo.toISOString().split('T')[0]}`;
      }
      
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setSymptomHistory(data);
        setSymptomHistoryFilter(filter);
      }
    } catch (error) {
      console.error("Error fetching symptom history:", error);
    } finally {
      setIsLoadingSymptomHistory(false);
    }
  };

  // Log Mood
  const handleLogMood = async () => {
    setIsLoading(true);
    try {
      const res = await fetch("http://localhost:8000/moods", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          mood_type: mood || undefined,
          description: moodDescription,
          intensity: moodIntensity || undefined,
        }),
      });
  
      const moodData = await res.json();
  
      setAffirmation(moodData.affirmation);
      setPepTalk(moodData.pep_talk);
      
      if (moodData.affirmation) {
        localStorage.setItem("lastAffirmation", moodData.affirmation);
        localStorage.setItem("lastAffirmationDate", new Date().toISOString());
      }

      // Refresh mood history if it's currently being shown
      if (moodHistoryFilter) {
        fetchMoodHistory(moodHistoryFilter);
      }

    } catch (error) {
      console.error("Error fetching mood data:", error);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Log Mood for a specific day
  const handleLogMoodForDay = async () => {
    setIsLoading(true);
    try {
      const res = await fetch("http://localhost:8000/moods", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          mood_type: mood || undefined,
          description: moodDescription,
          intensity: moodIntensity || undefined,
          date: moodDate,
        }),
      });
    
      const moodData = await res.json();
    
      setAffirmation(moodData.affirmation);
      setPepTalk(moodData.pep_talk);
      
      if (moodData.affirmation) {
        localStorage.setItem("lastAffirmation", moodData.affirmation);
        localStorage.setItem("lastAffirmationDate", new Date().toISOString());
      }

      // Refresh mood history if it's currently being shown
      if (moodHistoryFilter) {
        fetchMoodHistory(moodHistoryFilter);
      }

    } catch (error) {
      console.error("Error fetching mood data:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // Log Symptom
  const handleLogSymptom = async () => {
    setIsAdviceLoading(true);
    try {
      const res = await fetch("http://localhost:8000/symptoms", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          description: symptom,
        }),
      });
      const data = await res.json();
      setAdvice(data.advice);

      // Refresh symptom history if it's currently being shown
      if (symptomHistoryFilter) {
        fetchSymptomHistory(symptomHistoryFilter);
      }
    } catch (error) {
      console.error("Error logging symptom or fetching advice:", error);
    } finally {
      setIsAdviceLoading(false);
    }
  };
  

  // Log Symptom for a specific day
  const handleLogSymptomForDay = async () => {
    setIsAdviceLoading(true);
    try {
      const res = await fetch("http://localhost:8000/symptoms", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          description: symptom,
          date: symptomDate,
        }),
      });
      const data = await res.json();
      setAdvice(data.advice);

      // Refresh symptom history if it's currently being shown
      if (symptomHistoryFilter) {
        fetchSymptomHistory(symptomHistoryFilter);
      }
    } catch (error) {
      console.error("Error logging symptom or fetching advice:", error);
    } finally {
      setIsAdviceLoading(false);
    }
  };
  
  // Delete mood log
  const handleDeleteMood = async (moodId: string) => {
    setDeletingMoodId(moodId);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`http://localhost:8000/moods/${moodId}`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });
      
      if (res.ok) {
        // Remove from local state
        setMoodHistory(prev => prev.filter(log => log.id !== moodId));
      } else {
        console.error("Failed to delete mood log");
      }
    } catch (error) {
      console.error("Error deleting mood log:", error);
    } finally {
      setDeletingMoodId(null);
    }
  };

  // Delete symptom log
  const handleDeleteSymptom = async (symptomId: string) => {
    setDeletingSymptomId(symptomId);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`http://localhost:8000/symptoms/${symptomId}`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });
      
      if (res.ok) {
        // Remove from local state
        setSymptomHistory(prev => prev.filter(log => log.id !== symptomId));
      } else {
        console.error("Failed to delete symptom log");
      }
    } catch (error) {
      console.error("Error deleting symptom log:", error);
    } finally {
      setDeletingSymptomId(null);
    }
  };

  const moodTypes = [
    "happy",
    "sad",
    "anxious",
    "angry",
    "neutral",
    "tired",
    "stressed",
    "depressed",
  ];

  return (
    <div>
      <h1 style={{ fontWeight: "normal" }}>Log Mood / Symptom</h1>
      <div
        style={{
          display: "flex",
          gap: "2rem",
          marginTop: "2rem",
        }}
      >
        {/* Log Mood Column */}
        <div
          style={{
            flex: 1,
            background: "#f4f4f4",
            padding: "1rem",
            borderRadius: "8px",
            minHeight: "200px",
          }}
        >
          <h2 style={{ fontWeight: "normal" }}>Log Mood</h2>
          <textarea
            value={moodDescription}
            onChange={(e) => setMoodDescription(e.target.value)}
            placeholder="Describe your mood..."
            style={{ width: "100%", minHeight: "100px", padding: "0.5rem" }}
          />
          <label style={{ display: "block", marginBottom: "0.5rem" }}>
            Mood Type: <span style={{ color: "#666", fontSize: "0.9rem" }}>(Optional)</span>
            <select
              value={mood}
              onChange={(e) => setMood(e.target.value)}
              style={{ marginLeft: "0.5rem", padding: "0.25rem" }}
            >
              <option value="">Select mood type (optional)</option>
              {moodTypes.map((type) => (
                <option key={type} value={type}>
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </option>
              ))}
            </select>
          </label>
          <label style={{ display: "block", marginBottom: "0.5rem" }}>
            Intensity: <span style={{ color: "#666", fontSize: "0.9rem" }}>(Optional)</span>
            <select
              value={moodIntensity}
              onChange={(e) => setMoodIntensity(Number(e.target.value))}
              style={{ marginLeft: "0.5rem", padding: "0.25rem" }}
            >
              <option value="">Select intensity (optional)</option>
              {[...Array(10)].map((_, i) => (
                <option key={i + 1} value={i + 1}>
                  {i + 1}
                </option>
              ))}
            </select>
          </label>
          <button
            onClick={handleLogMood}
            disabled={!moodDescription.trim()}
            style={{
              marginTop: "1rem",
              padding: "0.3rem 0.8rem",
              background: "#666666",
              color: "#fff",
              border: "none",
              borderRadius: "4px",
              cursor: moodDescription.trim() ? "pointer" : "not-allowed",
              opacity: moodDescription.trim() ? 1 : 0.5,
              fontSize: "0.9rem"
            }}
          >
            Log
          </button>
          <div style={{ marginTop: "1.5rem" }}>
            <DatePicker
              selected={moodDate ?? undefined}
              onChange={(date) => setMoodDate(date)}
              dateFormat="yyyy-MM-dd"
              placeholderText="Log for a different day"
            />
            <button
              onClick={handleLogMoodForDay}
              disabled={!moodDescription.trim() || !moodDate}
              style={{
                marginLeft: "1rem",
                padding: "0.3rem 0.8rem",
                background: "#666666",
                color: "#fff",
                border: "none",
                borderRadius: "4px",
                cursor: moodDescription.trim() && moodDate ? "pointer" : "not-allowed",
                opacity: moodDescription.trim() && moodDate ? 1 : 0.5,
                fontSize: "0.9rem"
              }}
            >
              Log for this day
            </button>
          </div>

          {/* Pep Talk Window */}
          <div
            style={{
              marginTop: "2rem",
              background: "#fff",
              borderRadius: "8px",
              padding: "1rem",
              minHeight: "100px",
              boxShadow: "0 2px 8px rgba(0,0,0,0.05)",
            }}
          >
            <div style={{ fontWeight: "bold", marginBottom: "0.5rem" }}>
              Pep Talk
            </div>
          {isLoading ? (
            <div style={{ textAlign: "center", padding: "1rem" }}>
              <span>Loading...</span>
            </div>
          ) : (
            <div style={{ fontSize: "1.2rem" }}>
              {pepTalk ? <p>{pepTalk}</p> : <p>Log a mood to get a pep talk!</p>}
            </div>
          )}
          </div>
          {/* Affirmation Window */}
          <div
            style={{
              marginTop: "1rem",
              background: "#fff",
              borderRadius: "8px",
              padding: "1rem",
              minHeight: "100px",
              boxShadow: "0 2px 8px rgba(0,0,0,0.05)",
            }}
          >
            <div style={{ fontWeight: "bold", marginBottom: "0.5rem" }}>
              Affirmation
            </div>
          {isLoading ? (
            <div style={{ textAlign: "center", padding: "1rem" }}>
              <span>Loading...</span>
            </div>
          ) : (
            <div style={{ fontSize: "1.2rem" }}>
              {affirmation ? <p>{affirmation}</p> : <p>Log a mood to get an affirmation!</p>}
            </div>
          )}
          </div>
        </div>

        {/* Log Symptom Column */}
        <div
          style={{
            flex: 1,
            background: "#f4f4f4",
            padding: "1rem",
            borderRadius: "8px",
            minHeight: "200px",
          }}
        >
          <h2 style={{ fontWeight: "normal" }}>Log Symptom</h2>
          <textarea
            value={symptom}
            onChange={(e) => setSymptom(e.target.value)}
            placeholder="Describe your symptom..."
            style={{ width: "100%", minHeight: "100px", padding: "0.5rem" }}
          />
          <button
            onClick={handleLogSymptom}
            disabled={!symptom}
            style={{
              marginTop: "1rem",
              padding: "0.3rem 0.8rem",
              background: "#666666",
              color: "#fff",
              border: "none",
              borderRadius: "4px",
              cursor: symptom ? "pointer" : "not-allowed",
              opacity: symptom ? 1 : 0.5,
              fontSize: "0.9rem"
            }}
          >
            Log
          </button>
          <div style={{ marginTop: "1.5rem" }}>
            <DatePicker
              selected={symptomDate ?? undefined}
              onChange={(date) => setSymptomDate(date)}
              dateFormat="yyyy-MM-dd"
              placeholderText="Log for a different day"
            />
            <button
              onClick={handleLogSymptomForDay}
              disabled={!symptom || !symptomDate}
              style={{
                marginLeft: "1rem",
                padding: "0.3rem 0.8rem",
                background: "#666666",
                color: "#fff",
                border: "none",
                borderRadius: "4px",
                cursor: symptom && symptomDate ? "pointer" : "not-allowed",
                opacity: symptom && symptomDate ? 1 : 0.5,
                fontSize: "0.9rem"
              }}
            >
              Log for this day
            </button>
          </div>

          {/* Advice Window */}
          <div
            style={{
              marginTop: "2rem",
              background: "#fff",
              borderRadius: "8px",
              padding: "1rem",
              minHeight: "100px",
              boxShadow: "0 2px 8px rgba(0,0,0,0.05)",
            }}
          >
            <div style={{ fontWeight: "bold", marginBottom: "0.5rem" }}>
              Advice
            </div>
            {isAdviceLoading ? (
              <div style={{ textAlign: "center", padding: "1rem" }}>
                <span>Loading...</span>
              </div>
            ) : (
              <div style={{ fontSize: "1.2rem" }}>
                {advice ? <p>{advice}</p> : <p>Log a symptom to get advice!</p>}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* History Sections - Moved to bottom */}
      <div
        style={{
          display: "flex",
          gap: "2rem",
          marginTop: "2rem",
        }}
      >
        {/* Mood History Section */}
        <div
          style={{
            flex: 1,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1rem" }}>
            <h3 style={{ fontWeight: "normal", margin: 0 }}>Show mood log history</h3>
            <button
              onClick={() => fetchMoodHistory('30days')}
              disabled={isLoadingMoodHistory}
              style={{
                padding: "0.3rem 0.8rem",
                background: moodHistoryFilter === '30days' ? "#90EE90" : "#d3d3d3",
                color: moodHistoryFilter === '30days' ? "#000" : "#666",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
                fontSize: "0.9rem"
              }}
            >
              Last 30 days
            </button>
            <button
              onClick={() => fetchMoodHistory('all')}
              disabled={isLoadingMoodHistory}
              style={{
                padding: "0.3rem 0.8rem",
                background: moodHistoryFilter === 'all' ? "#90EE90" : "#d3d3d3",
                color: moodHistoryFilter === 'all' ? "#000" : "#666",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
                fontSize: "0.9rem"
              }}
            >
              All
            </button>
          </div>
          
          {/* Mood History Display */}
          {moodHistoryFilter && (
            <div style={{
              background: "#fff",
              borderRadius: "8px",
              padding: "1rem",
              maxHeight: "300px",
              overflowY: "auto",
              boxShadow: "0 2px 8px rgba(0,0,0,0.05)",
            }}>
              {isLoadingMoodHistory ? (
                <div style={{ textAlign: "center", padding: "1rem" }}>
                  <span>Loading...</span>
                </div>
              ) : moodHistory.length === 0 ? (
                <div style={{ textAlign: "center", padding: "1rem", color: "#666" }}>
                  No mood logs found
                </div>
              ) : (
                <div>
                  {moodHistory
                    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
                    .map((log) => (
                      <div key={log.id} style={{
                        borderBottom: "1px solid #eee",
                        padding: "0.5rem 0",
                        marginBottom: "0.5rem",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "flex-start"
                      }}>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: "bold", fontSize: "0.9rem" }}>
                            {new Date(log.created_at).toLocaleDateString()}
                          </div>
                          <div style={{ marginTop: "0.25rem" }}>
                            {log.description}
                          </div>
                          {log.mood_type && (
                            <div style={{ fontSize: "0.8rem", color: "#666", marginTop: "0.25rem" }}>
                              Type: {log.mood_type}
                            </div>
                          )}
                          {log.intensity && (
                            <div style={{ fontSize: "0.8rem", color: "#666" }}>
                              Intensity: {log.intensity}/10
                            </div>
                          )}
                        </div>
                        <button
                          onClick={() => handleDeleteMood(log.id)}
                          disabled={deletingMoodId === log.id}
                          style={{
                            background: "none",
                            border: "none",
                            color: "#dc3545",
                            cursor: "pointer",
                            padding: "0.25rem",
                            marginLeft: "0.5rem",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            opacity: deletingMoodId === log.id ? 0.5 : 1
                          }}
                          title="Delete mood log"
                        >
                          {deletingMoodId === log.id ? (
                            <span style={{ fontSize: "0.8rem" }}>...</span>
                          ) : (
                            <FaTrash size={14} />
                          )}
                        </button>
                      </div>
                    ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Symptom History Section */}
        <div
          style={{
            flex: 1,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1rem" }}>
            <h3 style={{ fontWeight: "normal", margin: 0 }}>Show symptom log history</h3>
            <button
              onClick={() => fetchSymptomHistory('30days')}
              disabled={isLoadingSymptomHistory}
              style={{
                padding: "0.3rem 0.8rem",
                background: symptomHistoryFilter === '30days' ? "#90EE90" : "#d3d3d3",
                color: symptomHistoryFilter === '30days' ? "#000" : "#666",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
                fontSize: "0.9rem"
              }}
            >
              Last 30 days
            </button>
            <button
              onClick={() => fetchSymptomHistory('all')}
              disabled={isLoadingSymptomHistory}
              style={{
                padding: "0.3rem 0.8rem",
                background: symptomHistoryFilter === 'all' ? "#90EE90" : "#d3d3d3",
                color: symptomHistoryFilter === 'all' ? "#000" : "#666",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
                fontSize: "0.9rem"
              }}
            >
              All
            </button>
          </div>
          
          {/* Symptom History Display */}
          {symptomHistoryFilter && (
            <div style={{
              background: "#fff",
              borderRadius: "8px",
              padding: "1rem",
              maxHeight: "300px",
              overflowY: "auto",
              boxShadow: "0 2px 8px rgba(0,0,0,0.05)",
            }}>
              {isLoadingSymptomHistory ? (
                <div style={{ textAlign: "center", padding: "1rem" }}>
                  <span>Loading...</span>
                </div>
              ) : symptomHistory.length === 0 ? (
                <div style={{ textAlign: "center", padding: "1rem", color: "#666" }}>
                  No symptom logs found
                </div>
              ) : (
                <div>
                  {symptomHistory
                    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
                    .map((log) => (
                      <div key={log.id} style={{
                        borderBottom: "1px solid #eee",
                        padding: "0.5rem 0",
                        marginBottom: "0.5rem",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "flex-start"
                      }}>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: "bold", fontSize: "0.9rem" }}>
                            {new Date(log.created_at).toLocaleDateString()}
                          </div>
                          <div style={{ marginTop: "0.25rem" }}>
                            {log.description}
                          </div>
                        </div>
                        <button
                          onClick={() => handleDeleteSymptom(log.id)}
                          disabled={deletingSymptomId === log.id}
                          style={{
                            background: "none",
                            border: "none",
                            color: "#dc3545",
                            cursor: "pointer",
                            padding: "0.25rem",
                            marginLeft: "0.5rem",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            opacity: deletingSymptomId === log.id ? 0.5 : 1
                          }}
                          title="Delete symptom log"
                        >
                          {deletingSymptomId === log.id ? (
                            <span style={{ fontSize: "0.8rem" }}>...</span>
                          ) : (
                            <FaTrash size={14} />
                          )}
                        </button>
                      </div>
                    ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}