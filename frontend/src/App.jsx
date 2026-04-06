import { useState, useCallback } from "react"
import ForceGraph2D from "react-force-graph-2d"
import ReactMarkdown from "react-markdown"
import "./App.css"

export default function App() {
  const [query, setQuery] = useState("")
  const [loading, setLoading] = useState(false)
  const [report, setReport] = useState(null)
  const [graph, setGraph] = useState(null)
  const [error, setError] = useState(null)

  async function investigate() {
    if (!query.trim()) return
    setLoading(true)
    setError(null)
    setReport(null)
    setGraph(null)

    try {
      const response = await fetch("http://127.0.0.1:8000/investigate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": import.meta.env.VITE_API_KEY
        },
        body: JSON.stringify({ query })
      })
      const data = await response.json()
      setReport(data.report)
      setGraph(data.graph)
    } catch (err) {
      setError("Investigation failed. Is the API server running?")
    } finally {
      setLoading(false)
    }
  }

  const nodeColor = useCallback(node => {
    if (node.type === "company") return "#4f46e5"
    if (node.type === "person") return "#059669"
    return "#6b7280"
  }, [])

  return (
    <div style={{ minHeight: "100vh", background: "#0f172a", color: "#f1f5f9", fontFamily: "system-ui, sans-serif" }}>
      
      <header style={{ borderBottom: "1px solid #1e293b", padding: "1rem 2rem", display: "flex", alignItems: "center", gap: "1rem" }}>
        <h1 style={{ margin: 0, fontSize: "1.5rem", fontWeight: 700, color: "#f1f5f9" }}>
          Trace
        </h1>
        <span style={{ color: "#64748b", fontSize: "0.875rem" }}>
          Entity Investigation Tool
        </span>
      </header>

      <main style={{ maxWidth: "1200px", margin: "0 auto", padding: "2rem" }}>
        <div style={{ marginBottom: "2rem" }}>
          <label htmlFor="search-input" style={{ display: "block", marginBottom: "0.5rem", color: "#94a3b8", fontSize: "0.875rem" }}>
            Enter a company name, person, or domain to investigate
          </label>
          <div style={{ display: "flex", gap: "0.75rem" }}>
            <input
              id="search-input"
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === "Enter" && investigate()}
              placeholder="e.g. Ajay Gupta"
              aria-label="Search query"
              style={{
                flex: 1,
                padding: "0.75rem 1rem",
                background: "#1e293b",
                border: "1px solid #334155",
                borderRadius: "0.5rem",
                color: "#f1f5f9",
                fontSize: "1rem",
                outline: "none"
              }}
            />
            <button
              onClick={investigate}
              disabled={loading}
              aria-label="Run investigation"
              style={{
                padding: "0.75rem 1.5rem",
                background: loading ? "#334155" : "#4f46e5",
                color: "#f1f5f9",
                border: "none",
                borderRadius: "0.5rem",
                fontSize: "1rem",
                cursor: loading ? "not-allowed" : "pointer",
                fontWeight: 600
              }}
            >
              {loading ? "Investigating..." : "Investigate"}
            </button>
          </div>
        </div>

        {error && (
          <div role="alert" style={{ padding: "1rem", background: "#450a0a", border: "1px solid #991b1b", borderRadius: "0.5rem", color: "#fca5a5", marginBottom: "1.5rem" }}>
            {error}
          </div>
        )}

        {loading && (
          <div aria-live="polite" style={{ color: "#64748b", textAlign: "center", padding: "3rem" }}>
            Running investigation — this may take 15-30 seconds...
          </div>
        )}

        {graph && graph.nodes.length > 0 && (
          <div style={{ marginBottom: "2rem", border: "1px solid #1e293b", borderRadius: "0.75rem", overflow: "hidden" }}>
            <div style={{ padding: "0.75rem 1rem", background: "#1e293b", fontSize: "0.875rem", color: "#94a3b8" }}>
              Relationship Graph — <span style={{ color: "#4f46e5" }}>■</span> Company &nbsp; <span style={{ color: "#059669" }}>■</span> Person
            </div>
            <ForceGraph2D
              graphData={graph}
              nodeLabel="name"
              nodeColor={nodeColor}
              linkLabel="label"
              width={1150}
              height={400}
              backgroundColor="#0f172a"
              nodeRelSize={6}
              linkColor={() => "#334155"}
            />
          </div>
        )}

        {report && (
          <div style={{
            background: "#1e293b",
            border: "1px solid #334155",
            borderRadius: "0.75rem",
            padding: "1.5rem 2rem",
            lineHeight: 1.7,
            textAlign: "left"
          }}>
            <div className="report">
              <ReactMarkdown>{report}</ReactMarkdown>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}