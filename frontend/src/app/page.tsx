'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { FaCheck, FaTimes, FaTrash, FaEdit } from "react-icons/fa";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";


const statusColumns = [
  { key: "pending", label: "Pending" },
  { key: "completed", label: "Completed" },
  { key: "cancelled", label: "Cancelled" },
] as const;

type Task = { 
  id: string; 
  title: string; 
  description?: string;
  status: string;
  due_date?: string | null;
  preferred_time?: string | null;
  created_at?: string;
  completed_at?: string | null;
  is_recurring?: boolean;
  recurrence_pattern?: string;
  recurrence_interval?: number;
  recurrence_end_date?: string | null;
};

// Helper function to format time from 24-hour to 12-hour format
const formatTime = (timeString: string): string => {
  if (!timeString) return "";
  
  try {
    const [hours, minutes] = timeString.split(':');
    const date = new Date();
    date.setHours(parseInt(hours), parseInt(minutes), 0);
    
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  } catch (error) {
    return timeString;
  }
};

export default function Home() {
  const { token } = useAuth();
  const [dailyQuote, setDailyQuote] = useState<string | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [taskDate, setTaskDate] = useState<Date | null>(new Date());
  const [completingId, setCompletingId] = useState<string | null>(null);
  // Update the taskFilter type to remove 'month'
  const [taskFilter, setTaskFilter] = useState<'today' | 'week' | 'all'>('today');
  
  // Add these new state variables for natural language task creation
  const [naturalLanguageInput, setNaturalLanguageInput] = useState("");
  const [naturalLanguageMessage, setNaturalLanguageMessage] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [isRescheduling, setIsRescheduling] = useState(false);
  const [rescheduleMessage, setRescheduleMessage] = useState("");

  // Task management states
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [dueDate, setDueDate] = useState<Date | null>(null);
  const [preferredTime, setPreferredTime] = useState("");
  const [message, setMessage] = useState("");
  const [isRecurring, setIsRecurring] = useState(false);
  const [recurrencePattern, setRecurrencePattern] = useState<"daily" | "weekly" | "monthly">("daily");
  const [recurrenceInterval, setRecurrenceInterval] = useState(1);
  const [recurrenceEndDate, setRecurrenceEndDate] = useState<Date | null>(null);
  const [error, setError] = useState("");
  const [cancellingId, setCancellingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Edit states
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editDueDate, setEditDueDate] = useState<Date | null>(null);
  const [editPreferredTime, setEditPreferredTime] = useState("");
  const [savingId, setSavingId] = useState<string | null>(null);

  // Fetch daily quote from localStorage or API
  const fetchDailyQuote = async () => {
    try {
      const storedQuote = localStorage.getItem("dailyQuote");
      const storedDate = localStorage.getItem("dailyQuoteDate");
      
      if (storedQuote && storedDate) {
        const quoteDate = new Date(storedDate);
        const today = new Date();
        const isToday = quoteDate.toDateString() === today.toDateString();
        
        if (isToday) {
          setDailyQuote(storedQuote);
          return;
        }
      }
      
      // Fetch new quote from API
      const res = await fetch("http://localhost:8000/moods/daily-quote");
      if (res.ok) {
        const data = await res.json();
        const quote = data.quote || null;
        setDailyQuote(quote);
        
        if (quote) {
          localStorage.setItem("dailyQuote", quote);
          localStorage.setItem("dailyQuoteDate", new Date().toISOString());
        }
      } else {
        console.error("Failed to fetch daily quote:", res.status, res.statusText);
        setDailyQuote("Every day is a new opportunity to be better than yesterday.");
      }
    } catch (error) {
      console.error("Error fetching daily quote:", error);
      setDailyQuote("Every day is a new opportunity to be better than yesterday.");
    }
  };

  // Update the fetch function to include period parameter
  const fetchTasks = async (date: Date | null, period: 'today' | 'week' | 'all') => {
    try {
      // Use the token from useAuth context instead of localStorage
      if (!token) {
        console.error("No authentication token available");
        return;
      }
      
      let url = "http://localhost:8000/tasks/due";
      const params = new URLSearchParams();
      
      if (period === 'all') {
        // For 'all', fetch from the general tasks endpoint
        const res = await fetch("http://localhost:8000/tasks", { 
          headers: { 
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json"
          } 
        });
        
        if (res.ok) {
          setTasks(await res.json());
        } else if (res.status === 401) {
          console.error("Authentication failed - token may be invalid");
          localStorage.removeItem("token");
          window.location.href = '/login';
        } else {
          console.error("Failed to fetch all tasks:", res.status, res.statusText);
        }
        return;
      }
      
      // Handle 'today' and 'week' periods
      if (date) {
        params.append('due_by', date.toISOString());
      }
      params.append('period', period);
      
      if (params.toString()) {
        url += `?${params.toString()}`;
      }
      
      const res = await fetch(url, { 
        headers: { 
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        } 
      });
      
      if (res.ok) {
        setTasks(await res.json());
      } else if (res.status === 401) {
        console.error("Authentication failed - token may be invalid");
        localStorage.removeItem("token");
        window.location.href = '/login';
      } else {
        console.error("Failed to fetch tasks:", res.status, res.statusText);
      }
    } catch (error) {
      console.error("Error fetching tasks:", error);
    }
  };

  // Add this function after handleCompleteTask
  const handleNaturalLanguageCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!naturalLanguageInput.trim()) return;
    
    setIsProcessing(true);
    setNaturalLanguageMessage("");
    
    try {
      if (!token) {
        setNaturalLanguageMessage("Authentication required");
        return;
      }
      
      const res = await fetch("http://localhost:8000/tasks/create-from-text", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({ user_input: naturalLanguageInput }),
      });
      
      if (!res.ok) {
        const data = await res.json();
        const errorMessage = typeof data.detail === 'string' 
          ? data.detail 
          : JSON.stringify(data.detail) || "Failed to create task";
        setNaturalLanguageMessage(errorMessage);
        return;
      }
      
      setNaturalLanguageMessage("Task created and scheduled!");
      setNaturalLanguageInput("");
      fetchTasks(taskDate, taskFilter); // Refresh tasks
    } catch (err) {
      setNaturalLanguageMessage("Failed to create task");
    } finally {
      setIsProcessing(false);
    }
  };

  // Reschedule expired calendar events
  const handleRescheduleExpired = async () => {
    setIsRescheduling(true);
    setRescheduleMessage("");
    try {
      if (!token) {
        setRescheduleMessage("Authentication required");
        return;
      }
      const res = await fetch("http://localhost:8000/tasks/reschedule-expired", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      });
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          setRescheduleMessage(`Rescheduled ${data.length} expired event${data.length > 1 ? "s" : ""}.`);
        } else {
          setRescheduleMessage("No expired calendar events to reschedule.");
        }
      } else {
        const data = await res.json().catch(() => ({}));
        setRescheduleMessage(data.detail || "Failed to reschedule.");
      }
    } catch (e) {
      setRescheduleMessage("Failed to reschedule.");
    } finally {
      setIsRescheduling(false);
    }
  };

  // Add this function after handleCompleteTask
  // Remove the separate fetchAllTasks function since it's now handled in fetchTasks

  // Task management functions
  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage("");
    try {
      if (!token) {
        setMessage("Authentication required");
        return;
      }
      
      const res = await fetch("http://localhost:8000/tasks", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          title,
          description,
          due_date: dueDate ? dueDate.toISOString() : null,
          preferred_time: preferredTime || null,
          is_recurring: isRecurring,
          recurrence_pattern: isRecurring ? recurrencePattern : null,
          recurrence_interval: isRecurring ? recurrenceInterval : null,
          recurrence_end_date: isRecurring && recurrenceEndDate ? recurrenceEndDate.toISOString() : null,
        }),
      });
      if (!res.ok) {
        const data = await res.json();
        setMessage(data.detail || "Failed to create task");
        return;
      }
      setMessage("Task created!");
      setTitle("");
      setDescription("");
      setDueDate(null);
      setPreferredTime("");
      setIsRecurring(false);
      setRecurrencePattern("daily");
      setRecurrenceInterval(1);
      setRecurrenceEndDate(null);
      fetchTasks(taskDate, taskFilter);
    } catch (err) {
      setMessage("Failed to create task");
    }
  };

  const handleCancelTask = async (taskId: string) => {
    setCancellingId(taskId);
    try {
      if (!token) {
        alert("Authentication required");
        return;
      }
      
      const res = await fetch(`http://localhost:8000/tasks/${taskId}`, {
        method: "PUT",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          status: "cancelled"
        })
      });
      if (!res.ok) {
        const data = await res.json();
        alert(data.detail || "Failed to cancel task");
        setCancellingId(null);
        return;
      }
      fetchTasks(taskDate, taskFilter);
    } catch (err) {
      alert("Failed to cancel task");
    } finally {
      setCancellingId(null);
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    setDeletingId(taskId);
    try {
      if (!token) {
        alert("Authentication required");
        return;
      }
      
      const res = await fetch(`http://localhost:8000/tasks/${taskId}`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${token}`,
        }
      });
      if (!res.ok) {
        const data = await res.json();
        alert(data.detail || "Failed to delete task");
        setDeletingId(null);
        return;
      }
      fetchTasks(taskDate, taskFilter);
    } catch (err) {
      alert("Failed to delete task");
    } finally {
      setDeletingId(null);
    }
  };

  const handleStartEdit = (task: Task) => {
    setEditingTask(task);
    setEditTitle(task.title);
    setEditDescription(task.description || "");
    setEditDueDate(task.due_date ? new Date(task.due_date) : null);
    setEditPreferredTime(task.preferred_time || "");
  };

  const handleCancelEdit = () => {
    setEditingTask(null);
    setEditTitle("");
    setEditDescription("");
    setEditDueDate(null);
    setEditPreferredTime("");
  };

  const handleSaveEdit = async () => {
    if (!editingTask) return;
    
    setSavingId(editingTask.id);
    try {
      if (!token) {
        alert("Authentication required");
        return;
      }
      
      const res = await fetch(`http://localhost:8000/tasks/${editingTask.id}`, {
        method: "PUT",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          title: editTitle,
          description: editDescription,
          due_date: editDueDate ? editDueDate.toISOString() : null,
          preferred_time: editPreferredTime || null,
        })
      });
      
      if (!res.ok) {
        const data = await res.json();
        alert(data.detail || "Failed to update task");
        return;
      }
      
      handleCancelEdit();
      fetchTasks(taskDate, taskFilter);
    } catch (err) {
      alert("Failed to update task");
    } finally {
      setSavingId(null);
    }
  };

  // Add this function after handleCompleteTask
  const handleCompleteTask = async (taskId: string) => {
    setCompletingId(taskId);
    try {
      if (!token) {
        alert("Authentication required");
        return;
      }
      
      const res = await fetch(`http://localhost:8000/tasks/${taskId}/complete`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      });
      if (!res.ok) {
        const data = await res.json();
        alert(data.detail || "Failed to complete task");
        setCompletingId(null);
        return;
      }
      fetchTasks(taskDate, taskFilter);
    } catch (err) {
      alert("Failed to complete task");
    } finally {
      setCompletingId(null);
    }
  };


  // Sort tasks by due date and preferred time
  const sortedTasks = [...tasks].sort((a, b) => {
    // If both tasks have due dates
    if (a.due_date && b.due_date) {
      const dateA = new Date(a.due_date).getTime();
      const dateB = new Date(b.due_date).getTime();
      
      // If dates are different, sort by date
      if (dateA !== dateB) {
        return dateA - dateB;
      }
      
      // If dates are the same, sort by preferred time
      if (a.preferred_time && b.preferred_time) {
        return a.preferred_time.localeCompare(b.preferred_time);
      }
      
      // If only one has preferred time, prioritize the one with time
      if (a.preferred_time && !b.preferred_time) return -1;
      if (!a.preferred_time && b.preferred_time) return 1;
      
      // If neither has preferred time, maintain original order
      return 0;
    }
    
    // If only one has a due date, prioritize the one with due date
    if (a.due_date && !b.due_date) return -1;
    if (!a.due_date && b.due_date) return 1;
    
    // If neither has due date, sort by preferred time if available
    if (a.preferred_time && b.preferred_time) {
      return a.preferred_time.localeCompare(b.preferred_time);
    }
    
    // If only one has preferred time, prioritize the one with time
    if (a.preferred_time && !b.preferred_time) return -1;
    if (!a.preferred_time && b.preferred_time) return 1;
    
    // If neither has due date or preferred time, maintain original order
    return 0;
  });

  // Separate useEffect for initial data loading
  useEffect(() => {
    const loadData = async () => {
      if (!token) {
        setLoading(false);
        return;
      }
      
      setLoading(true);
      const today = new Date();
      
      try {
        await Promise.all([
          fetchDailyQuote(),
          fetchTasks(today, 'today')  // Keep 'today' as default
        ]);
      } catch (error) {
        console.error("Error loading initial data:", error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [token]); // Only depend on token

  // Show loading state while token is being validated
  if (loading) {
    return (
      <div style={{ 
        display: "flex", 
        justifyContent: "center", 
        alignItems: "center", 
        height: "100vh",
        fontSize: "1.2rem"
      }}>
        Loading your tasks...
      </div>
    );
  }

  // Show login prompt if no token
  if (!token) {
    return (
      <div style={{ 
        display: "flex", 
        justifyContent: "center", 
        alignItems: "center", 
        height: "100vh",
        flexDirection: "column",
        gap: "1rem"
      }}>
        <h2>Please log in to view your tasks</h2>
        <button 
          onClick={() => window.location.href = '/login'}
          style={{
            padding: "0.5rem 1rem",
            background: "#007bff",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer"
          }}
        >
          Go to Login
        </button>
      </div>
    );
  }

  return (
    <div style={{ padding: "1rem" }}>
      
      {/* Daily Quote Section */}
      <section style={{ marginBottom: "2rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <h3 style={{ margin: 0, fontWeight: "normal", marginBottom: 0 }}>Thought of the Day</h3>
          <div style={{
            background: "#f8f9fa",
            padding: "1rem",
            borderRadius: "8px",
            border: "1px solid #e9ecef",
            minHeight: "10px",
            display: "flex",
            alignItems: "center",
            flex: 1
          }}>
            {dailyQuote ? (
              <p style={{ 
                fontSize: "1.2rem", 
                margin: 0, 
                fontStyle: "italic",
                color: "#495057"
              }}>
                "{dailyQuote}"
              </p>
            ) : (
              <p style={{ 
                fontSize: "1.1rem", 
                margin: 0, 
                color: "#6c757d",
                fontStyle: "italic"
              }}>
                Loading your daily inspiration...
              </p>
            )}
          </div>
        </div>
      </section>

      {/* AI Task Creation */}
      <section style={{ marginBottom: "4rem" }}>
        <h3 style={{ marginTop: "4rem", fontWeight: "normal", marginBottom: "1rem" }}>Create task and calendar event with NLP</h3>
        <form onSubmit={handleNaturalLanguageCreate}>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
            <div style={{ flex: 1 }}>
              <textarea
                placeholder="Describe your task..."
                value={naturalLanguageInput}
                onChange={e => setNaturalLanguageInput(e.target.value)}
                style={{ 
                  width: "100%", 
                  padding: "0.5rem", 
                  minHeight: "60px", 
                  resize: "vertical",
                  border: "1px solid #ddd",
                  borderRadius: "4px"
                }}
                required
              />
            </div>
            <button 
              type="submit" 
              disabled={!naturalLanguageInput.trim() || isProcessing}
              style={{
                padding: "0.5rem 0.8rem",
                background: naturalLanguageInput.trim() && !isProcessing ? "#28a745" : "#b3b3b3",
                color: "#fff",
                border: "none",
                borderRadius: "4px",
                cursor: naturalLanguageInput.trim() && !isProcessing ? "pointer" : "not-allowed",
                fontSize: "1rem",
                marginBottom: "0.4rem"
              }}
            >
              {isProcessing ? "Creating..." : "Create Task"}
            </button>
          </div>
        </form>
        {naturalLanguageMessage && (
          <div style={{ 
            marginTop: "1rem", 
            color: naturalLanguageMessage === "Task created and scheduled!" ? "green" : "red" 
          }}>
            {naturalLanguageMessage}
          </div>
        )}
      </section>


      {/* Task Management Section */}
      <section style={{ marginBottom: "2rem" }}>
        <div style={{ background: "#ffffff", minHeight: "50vh", padding: "0rem 2rem 2rem 2rem" }}>
          <div style={{ display: "flex", alignItems: "center", marginBottom: "1rem", marginLeft: '-1.5rem', marginTop: '3rem', gap: '0.2rem' }}>
            <h3 style={{ margin: 0, fontWeight: "normal", marginRight: "1rem" }}>Tasks</h3>
            
            {/* Move period filter buttons here */}
            <button 
              onClick={() => { 
                setTaskDate(new Date()); 
                setTaskFilter('today');
                fetchTasks(new Date(), 'today'); 
              }} 
              style={{ 
                marginRight: "0.3rem", 
                padding: "0.3rem 0.5rem",
                background: taskFilter === 'today' ? "#28a745" : "#b3b3b3",
                color: "#fff",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
                fontSize: "0.9rem"
              }}
            >
              Today
            </button>

            <button 
              onClick={() => { 
                const currentDate = new Date(); 
                setTaskDate(currentDate); 
                setTaskFilter('week');
                fetchTasks(currentDate, 'week'); 
              }} 
              style={{ 
                marginRight: "0.3rem", 
                padding: "0.3rem 0.5rem",
                background: taskFilter === 'week' ? "#28a745" : "#b3b3b3",
                color: "#fff",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
                fontSize: "0.9rem"
              }}
            >
              This Week
            </button>

            {/* Remove the "This Month" button entirely */}

            {/* Update the "All" button to use the updated fetchTasks function */}
            <button 
              onClick={() => { 
                setTaskDate(null); 
                setTaskFilter('all');
                fetchTasks(null, 'all'); 
              }} 
              style={{ 
                marginRight: "0.3rem", 
                padding: "0.3rem 0.5rem",
                background: taskFilter === 'all' ? "#28a745" : "#b3b3b3",
                color: "#fff",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
                fontSize: "0.9rem"
              }}
            >
              All
            </button>

            {/* Move reschedule button here */}
            <button 
              onClick={handleRescheduleExpired}
              disabled={isRescheduling}
              style={{ 
                marginRight: "0.5rem", 
                padding: "0.3rem 0.5rem",
                background: isRescheduling ? "#28a745" : "#b3b3b3",
                color: "#fff",
                border: "none",
                borderRadius: "4px",
                cursor: isRescheduling ? "not-allowed" : "pointer",
                fontSize: "0.9rem"
              }}
            >
              {isRescheduling ? "Rescheduling..." : "Reschedule expired calendar events"}
            </button>
            {rescheduleMessage && (
              <div style={{ marginTop: "0.5rem", color: rescheduleMessage.startsWith("Rescheduled") ? "green" : "#6c757d" }}>
                {rescheduleMessage}
              </div>
            )}
          </div>
          {error && <div style={{ color: "red", marginBottom: "1rem" }}>{error}</div>}
          
          {/* Column headers row */}
          <div style={{ display: "flex", gap: "2rem", marginBottom: "1rem", marginTop: "1.5rem" }}>
            {statusColumns.map(col => (
              <div key={col.key} style={{ flex: 1, textAlign: "center", fontSize: "1.1rem", color: "#737373" }}>
                {col.label}
              </div>
            ))}
          </div>
          
          {/* Columns */}
          <div style={{ display: "flex", gap: "2rem", marginLeft: '-1.5rem', marginRight: '-1.5rem' }}>
            {statusColumns.map(col => (
              <div
                key={col.key}
                style={{
                  flex: 1,
                  background: "#f2f2f2",
                  borderRadius: 8,
                  padding: "1rem"
                }}
              >
                <ul style={{ listStyle: "none", padding: 0 }}>
                  {sortedTasks
                    .filter(task => task.status === col.key)
                    .map(task => (
                      <li key={task.id} style={{ marginBottom: "0.5rem", paddingBottom: "0.5rem" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.1rem" }}>
                          {task.status === "completed" && (
                            <span style={{ 
                              color: "#4caf50",
                              fontSize: "1.2rem",
                              fontWeight: "bold"
                            }}>
                              ✓
                            </span>
                          )}
                          {task.status === "cancelled" && (
                            <button
                              onClick={() => handleDeleteTask(task.id)}
                              disabled={deletingId === task.id}
                              style={{
                                color: "#6c757d",
                                border: "none",
                                borderRadius: "50%",
                                width: "1rem",
                                height: "1rem",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                cursor: "pointer",
                                fontSize: "0.8rem",
                                position: "relative",
                                background: "transparent"
                              }}
                              title="Delete Task"
                            >
                              {deletingId === task.id ? (
                                <span style={{ fontSize: "0.7rem" }}>...</span>
                              ) : (
                                <FaTrash />
                              )}
                            </button>
                          )}
                          <div style={{
                            textDecoration: (task.status === "completed" || task.status === "cancelled") ? "line-through" : "none",
                            color: (task.status === "completed" || task.status === "cancelled") ? "#6c757d" : "inherit"
                          }}>
                            {task.preferred_time && (
                              <span style={{ 
                                color: (task.status === "completed" || task.status === "cancelled") ? "#6c757d" : "#666",
                                fontWeight: "normal",
                                marginRight: "0.5rem"
                              }}>
                                {formatTime(task.preferred_time)}
                              </span>
                            )}
                            <strong>{task.title}</strong>
                          </div>
                          {task.status !== "completed" && task.status !== "cancelled" && (
                            <div style={{ display: "flex", gap: "0rem" }}>
                              <button
                                onClick={() => handleCompleteTask(task.id)}
                                disabled={completingId === task.id}
                                style={{
                                  color: "#4caf50",
                                  border: "none",
                                  borderRadius: "50%",
                                  width: "1rem",
                                  height: "1rem",
                                  display: "flex",
                                  alignItems: "center",
                                  justifyContent: "center",
                                  cursor: "pointer",
                                  fontSize: "1rem",
                                  position: "relative",
                                  background: "transparent"
                                }}
                                title="Mark as Completed"
                              >
                                {completingId === task.id ? (
                                  <span style={{ fontSize: "0.7rem" }}>...</span>
                                ) : (
                                  <FaCheck />
                                )}
                              </button>
                              <button
                                onClick={() => handleCancelTask(task.id)}
                                disabled={cancellingId === task.id}
                                style={{
                                  color: "#f44336",
                                  border: "none",
                                  borderRadius: "50%",
                                  width: "1.5rem",
                                  height: "1rem",
                                  display: "flex",
                                  alignItems: "center",
                                  justifyContent: "center",
                                  cursor: "pointer",
                                  fontSize: "1rem",
                                  position: "relative",
                                  background: "transparent"
                                }}
                                title="Cancel Task"
                              >
                                {cancellingId === task.id ? (
                                  <span style={{ fontSize: "0.9rem" }}>...</span>
                                ) : (
                                  <FaTimes />
                                )}
                              </button>
                              <button
                                onClick={() => handleStartEdit(task)}
                                style={{
                                  color: "#66b0ff",
                                  border: "none",
                                  borderRadius: "50%",
                                  width: "1rem",
                                  height: "1rem",
                                  display: "flex",
                                  alignItems: "center",
                                  justifyContent: "center",
                                  cursor: "pointer",
                                  fontSize: "0.8rem",
                                  position: "relative",
                                  background: "transparent"
                                }}
                                title="Edit Task"
                              >
                                <FaEdit />
                              </button>
                              <button
                                onClick={() => handleDeleteTask(task.id)}
                                disabled={deletingId === task.id}
                                style={{
                                  color: "#6c757d",
                                  border: "none",
                                  borderRadius: "50%",
                                  width: "1rem",
                                  height: "1rem",
                                  display: "flex",
                                  alignItems: "center",
                                  justifyContent: "center",
                                  cursor: "pointer",
                                  fontSize: "0.8rem",
                                  position: "relative",
                                  background: "transparent"
                                }}
                                title="Delete Task"
                              >
                                {deletingId === task.id ? (
                                  <span style={{ fontSize: "0.7rem" }}>...</span>
                                ) : (
                                  <FaTrash />
                                )}
                              </button>
                            </div>
                          )}
                          {task.status === "completed" && (
                            <div style={{ display: "flex", gap: "0rem" }}>
                              <button
                                onClick={() => handleDeleteTask(task.id)}
                                disabled={deletingId === task.id}
                                style={{
                                  color: "#6c757d",
                                  border: "none",
                                  borderRadius: "50%",
                                  width: "1rem",
                                  height: "1rem",
                                  display: "flex",
                                  alignItems: "center",
                                  justifyContent: "center",
                                  cursor: "pointer",
                                  fontSize: "0.8rem",
                                  position: "relative",
                                  background: "transparent"
                                }}
                                title="Delete Task"
                              >
                                {deletingId === task.id ? (
                                  <span style={{ fontSize: "0.7rem" }}>...</span>
                                ) : (
                                  <FaTrash />
                                )}
                              </button>
                            </div>
                          )}
                        </div>
                        <div style={{ 
                          display: "flex", 
                          alignItems: "center", 
                          gap: "1rem", 
                          fontSize: "0.9em", 
                          color: (task.status === "completed" || task.status === "cancelled") ? "#6c757d" : "#666",
                          textDecoration: (task.status === "completed" || task.status === "cancelled") ? "line-through" : "none"
                        }}>
                          <span>{task.description}</span>
                          {task.due_date && (
                            <span style={{ color: (task.status === "completed" || task.status === "cancelled") ? "#6c757d" : "#888" }}>
                              Due: {new Date(task.due_date).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                      </li>
                    ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Edit Task Modal */}
      {editingTask && (
        <div style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: "rgba(0,0,0,0.5)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 1000
        }}>
          <div style={{
            background: "white",
            padding: "2rem",
            borderRadius: "8px",
            width: "500px",
            maxWidth: "90vw"
          }}>
            <h3 style={{ marginTop: 0, marginBottom: "1rem" }}>Edit Task</h3>
            
            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", marginBottom: "0.5rem" }}>Title:</label>
              <input
                type="text"
                value={editTitle}
                onChange={e => setEditTitle(e.target.value)}
                style={{ width: "100%", padding: "0.5rem" }}
                required
              />
            </div>
            
            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", marginBottom: "0.5rem" }}>Description:</label>
              <textarea
                value={editDescription}
                onChange={e => setEditDescription(e.target.value)}
                style={{ width: "100%", padding: "0.5rem", minHeight: "80px", resize: "vertical" }}
              />
            </div>
            
            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", marginBottom: "0.5rem" }}>Due Date:</label>
              <DatePicker
                selected={editDueDate}
                onChange={date => setEditDueDate(date)}
                dateFormat="yyyy-MM-dd"
                placeholderText="Select date"
                isClearable
              />
            </div>
            
            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", marginBottom: "0.5rem" }}>Preferred Time:</label>
              <input
                type="time"
                value={editPreferredTime}
                onChange={e => setEditPreferredTime(e.target.value)}
                style={{
                  padding: "0.5rem",
                  border: "1px solid #ccc",
                  borderRadius: "4px",
                  width: "100%"
                }}
              />
            </div>
            
            <div style={{ display: "flex", gap: "1rem", justifyContent: "flex-end" }}>
              <button
                onClick={handleCancelEdit}
                style={{
                  padding: "0.5rem 1rem",
                  background: "#6c757d",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer"
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleSaveEdit}
                disabled={!editTitle.trim() || savingId === editingTask.id}
                style={{
                  padding: "0.5rem 1rem",
                  background: editTitle.trim() && savingId !== editingTask.id ? "#66b0ff" : "#b3b3b3",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: editTitle.trim() && savingId !== editingTask.id ? "pointer" : "not-allowed"
                }}
              >
                {savingId === editingTask.id ? "Saving..." : "Save"}
              </button>
            </div>
          </div>
        </div>
      )}


      {/* Task Creation Form */}
      <section style={{ marginBottom: "2rem" }}>
        <h3 style={{ marginTop: "4rem", fontWeight: "normal", marginBottom: "1rem" }}>Create a Task</h3>
        <div style={{
          background: "#f4f4f4",
          borderRadius: 8,
          boxShadow: "0 2px 8px rgba(0,0,0,0.05)",
          padding: "2rem",
          marginBottom: '1.5rem'
        }}>
          <form onSubmit={handleCreateTask}>
            {/* Title and Due Date row */}
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '0.5rem', marginTop: '-1rem', marginLeft: '-1rem' }}>
              <div>
                <input
                  type="text"
                  placeholder="Title"
                  value={title}
                  onChange={e => setTitle(e.target.value)}
                  required
                  style={{ width: "300px", padding: "0.5rem" }}
                />
              </div>
              <label>
                Due Date:{" "}
                <DatePicker
                  selected={dueDate}
                  onChange={date => setDueDate(date)}
                  dateFormat="yyyy-MM-dd"
                  placeholderText="Select date"
                  isClearable
                />
              </label>
              <label>
                Preferred Time:{" "}
                <input
                  type="time"
                  value={preferredTime}
                  onChange={e => setPreferredTime(e.target.value)}
                  style={{
                    padding: "0.3rem",
                    border: "1px solid #ccc",
                    borderRadius: "4px",
                    fontSize: "0.9rem"
                  }}
                />
              </label>
            </div>

            {/* Description and Recurring Task row */}
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '-1rem', alignItems: 'flex-start', marginLeft: '-1rem' }}>
              <div>
                <textarea
                  placeholder="Description"
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  style={{ width: "300px", padding: "0.5rem", minHeight: "40px", resize: "vertical" }}
                />
              </div>
              <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.5rem' }}>
                  <label>
                    <input
                      type="checkbox"
                      checked={isRecurring}
                      onChange={e => setIsRecurring(e.target.checked)}
                      style={{ marginRight: "0.5rem" }}
                    />
                    Recurring Task
                  </label>
                  
                  {/* Recurring task options */}
                  {isRecurring && (
                    <div style={{ marginBottom: "0.5rem" }}>
                      <label>
                        Repeat:&nbsp;
                        <select
                          value={recurrencePattern}
                          onChange={e => setRecurrencePattern(e.target.value as "daily" | "weekly" | "monthly")}
                          style={{ marginRight: "1rem" }}
                        >
                          <option value="daily">Every day</option>
                          <option value="weekly">Every week</option>
                          <option value="monthly">Every month</option>
                        </select>
                      </label>
                      <label>
                        Every&nbsp;
                        <input
                          type="number"
                          min={1}
                          value={recurrenceInterval}
                          onChange={e => setRecurrenceInterval(Number(e.target.value))}
                          style={{ width: 60, marginRight: "0.5rem" }}
                        />
                        {recurrencePattern === "daily"
                          ? "day(s)"
                          : recurrencePattern === "weekly"
                          ? "week(s)"
                          : "month(s)"}
                      </label>
                      <label style={{ marginLeft: "1rem" }}>
                        End on:&nbsp;
                        <DatePicker
                          selected={recurrenceEndDate}
                          onChange={date => setRecurrenceEndDate(date)}
                          dateFormat="yyyy-MM-dd"
                          isClearable
                          placeholderText="No end date"
                        />
                      </label>
                    </div>
                  )}
                </div>
                
                <button 
                  type="submit" 
                  disabled={!title.trim()}
                  style={{
                    padding: "0.5rem 0.5rem",
                    background: title.trim() ? "#28a745" : "#b3b3b3",
                    color: "#fff",
                    border: "none",
                    borderRadius: "4px",
                    cursor: title.trim() ? "pointer" : "not-allowed",
                    fontSize: "1rem",
                    alignSelf: "flex-start",
                    marginTop: "0.5rem"
                  }}
                >
                  Create a Task
                </button>
              </div>
            </div>
          </form>
          {message && <div style={{ marginTop: "1rem", color: message === "Task created!" ? "green" : "red" }}>{message}</div>}
        </div>
      </section>
    </div>
  );
}