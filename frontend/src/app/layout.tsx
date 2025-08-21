import './globals.css'
import Sidebar from '../components/sidebar'
import { AuthProvider } from "../context/AuthContext";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, padding: 0 }}>
        <AuthProvider>
          <Sidebar />
          <main style={{ marginLeft: '200px', padding: '2rem' }}>
            {children}
          </main>
        </AuthProvider>
      </body>
    </html>
  )
}
