"use client";

import Link from 'next/link';
import React, { useState, useRef, useEffect } from "react";
import { FaUserCircle } from "react-icons/fa";
import { useAuth } from "@/context/AuthContext";

const menuItems = [
  { name: 'Home', path: '/' },
  {
    name: 'Moods & Symptoms',
    path: '/moods-symptoms',
    subItems: [
      { name: 'Log mood/symptom', path: '/moods-symptoms/log' },
      { name: 'Evaluate', path: '/moods-symptoms/evaluate' },
    ]
  },
  { name: 'Benefits', path: '/benefits' },
];

export default function Sidebar() {
  // Track which dropdown is open by name
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);
  const { user, logout } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close user dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <aside style={{
      width: '200px',
      height: '100vh',
      background: '#f4f4f4',
      padding: '1rem',
      boxSizing: 'border-box',
      position: 'fixed',
      left: 0,
      top: 0,
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between'
    }}>
      <nav>
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {menuItems.map(item => (
            <React.Fragment key={item.name}>
              <li style={{ margin: '1rem 0', display: 'flex', alignItems: 'center' }}>
                <Link href={item.path} style={{ textDecoration: 'none', color: '#333', flex: 1 }}>
                  {item.name}
                </Link>
                {item.subItems && (
                  <button
                    onClick={() =>
                      setOpenDropdown(openDropdown === item.name ? null : item.name)
                    }
                    style={{
                      background: 'none',
                      border: 'none',
                      padding: 0,
                      font: 'inherit',
                      color: '#333',
                      cursor: 'pointer',
                      marginLeft: '0.5rem'
                    }}
                    aria-label={openDropdown === item.name ? "Collapse" : "Expand"}
                  >
                    {openDropdown === item.name ? '▲' : '▼'}
                  </button>
                )}
              </li>
              {item.subItems && openDropdown === item.name && (
                <ul style={{ listStyle: 'none', paddingLeft: '1.5rem', marginTop: '-0.5rem', marginBottom: '0.5rem' }}>
                  {item.subItems.map(sub => (
                    <li key={sub.name} style={{ margin: '0.5rem 0' }}>
                      <Link href={sub.path} style={{ textDecoration: 'none', color: '#555' }}>
                        {sub.name}
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </React.Fragment>
          ))}
        </ul>
      </nav>
      {/* User Icon or Log In at the bottom */}
      <div style={{ padding: "1rem 0 0 0", position: "relative" }} ref={dropdownRef}>
        {user ? (
          <>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                cursor: "pointer",
                gap: "0.5rem",
                color: "#333"
              }}
              onClick={() => setDropdownOpen((open) => !open)}
            >
              <FaUserCircle size={28} />
              <span>{user.email}</span>
            </div>
            {dropdownOpen && (
              <div
                style={{
                  position: "absolute",
                  left: 0,
                  bottom: "2.5rem",
                  background: "#fff",
                  color: "#222",
                  borderRadius: 8,
                  boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                  minWidth: 160,
                  zIndex: 200,
                  padding: "0.5rem 0",
                }}
              >
                <div style={{ padding: "0.5rem 1rem", cursor: "default", borderBottom: "1px solid #eee" }}>
                  <strong>User Info</strong>
                  <div style={{ fontSize: "0.9em" }}>{user.email}</div>
                </div>
                <div
                  style={{ padding: "0.5rem 1rem", cursor: "pointer", borderBottom: "1px solid #eee" }}
                  onClick={() => {
                    window.location.href = "/settings";
                  }}
                >
                  Settings
                </div>
                <div
                  style={{ padding: "0.5rem 1rem", cursor: "pointer", color: "red" }}
                  onClick={logout}
                >
                  Logout
                </div>
              </div>
            )}
          </>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <button
              style={{
                width: "100%",
                padding: "0.75rem",
                background: "#333",
                color: "#fff",
                border: "none",
                borderRadius: "8px",
                cursor: "pointer",
                fontSize: "1rem"
              }}
              onClick={() => window.location.href = "/login"}
            >
              Log In
            </button>
            <button
              style={{
                width: "100%",
                padding: "0.75rem",
                background: "#888",
                color: "#fff",
                border: "none",
                borderRadius: "8px",
                cursor: "pointer",
                fontSize: "1rem"
              }}
              onClick={() => window.location.href = "/register"}
            >
              Register
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}