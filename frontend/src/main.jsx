import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { Check, ChevronRight, CircleHelp, Sparkles, Send, RotateCcw } from "lucide-react";
import "./styles.css";

const API = "http://localhost:8000/api";

function App() {
  const [session, setSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [mode, setMode] = useState("text");
  const [evidence, setEvidence] = useState([]);
  const [loading, setLoading] = useState(false);
  const [complete, setComplete] = useState(false);

  const start = async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/start`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({assessment_id: "seasons"})
      });
      const data = await r.json();
      setSession(data.session_id);
      setEvidence(data.evidence);
      setMessages([
        { role: "proof", text: data.message },
        { role: "proof", text: data.question, mode: data.mode, question: true }
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { start(); }, []);

  const send = async (forced = null) => {
    const value = forced ?? input.trim();
    if (!value || !session || loading || complete) return;
    setInput("");
    setMessages(prev => [...prev, { role: "user", text: value }]);
    setLoading(true);
    try {
      const r = await fetch(`${API}/answer`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({session_id: session, answer: value, mode})
      });
      const data = await r.json();
      setEvidence(data.evidence || []);
      if (data.reply) setMessages(prev => [...prev, { role: "proof", text: data.reply }]);
      if (data.complete) {
        setComplete(true);
        setMessages(prev => [...prev, { role: "proof", text: data.summary, result: true }]);
      } else if (data.question) {
        setMessages(prev => [...prev, { role: "proof", text: data.question, question: true, mode: data.mode }]);
      }
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setMessages([]);
    setComplete(false);
    setEvidence([]);
    setSession(null);
    start();
  };

  const demonstrated = evidence.filter(x => x.status === "demonstrated").length;
  const progress = evidence.length ? Math.round((demonstrated / evidence.length) * 100) : 0;

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="logo">P</div>
          <div>
            <strong>PROOF</strong>
            <span>show what you know</span>
          </div>
        </div>
        <button className="reset" onClick={reset}><RotateCcw size={15}/> New attempt</button>
      </header>

      <main className="layout">
        <section className="chat-panel">
          <div className="intro">
            <div className="eyebrow"><Sparkles size={15}/> ADAPTIVE ASSESSMENT</div>
            <h1>You don't have to answer<br/>the usual way.</h1>
            <p>PROOF keeps the learning goal the same while finding a better way to see what you understand.</p>
          </div>

          <div className="messages">
            {messages.map((m, i) => (
              <div key={i} className={`row ${m.role}`}>
                {m.role === "proof" && <div className="avatar">P</div>}
                <div className={`bubble ${m.result ? "result" : ""}`}>
                  {m.text}
                  {m.question && m.mode === "choice" && (
                    <div className="choices">
                      <button onClick={() => send("Yes, I think that is correct.")}>Yes</button>
                      <button onClick={() => send("No, I don't think that is correct.")}>No</button>
                      <button onClick={() => send("I'm not sure.")}>I'm not sure</button>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && <div className="row proof"><div className="avatar">P</div><div className="bubble typing">Thinking<span>•••</span></div></div>}
          </div>

          {!complete && (
            <div className="composer">
              <div className="modebar">
                <button className={mode==="text" ? "active":""} onClick={()=>setMode("text")}>Type</button>
                <button className={mode==="rough" ? "active":""} onClick={()=>setMode("rough")}>Rough answer</button>
                <button className="stuck" onClick={()=>setInput("I know the answer, but I can't explain it.")}><CircleHelp size={14}/> I know it, but I'm stuck</button>
              </div>
              <div className="inputrow">
                <input
                  value={input}
                  onChange={e=>setInput(e.target.value)}
                  onKeyDown={e=>e.key==="Enter" && send()}
                  placeholder="Answer in whatever way feels easiest…"
                />
                <button className="send" onClick={()=>send()} disabled={!input.trim() || loading}><Send size={17}/></button>
              </div>
            </div>
          )}
        </section>

        <aside className="evidence-panel">
          <div className="side-title">
            <div>
              <span className="eyebrow">YOUR EVIDENCE</span>
              <h2>What you've shown</h2>
            </div>
            <div className="score">{progress}%</div>
          </div>

          <div className="progress"><div style={{width:`${progress}%`}}/></div>

          <p className="side-note">
            PROOF is checking the ideas behind the answer — not just how well the answer is written.
          </p>

          <div className="evidence-list">
            {evidence.map(item => (
              <div className={`evidence ${item.status === "demonstrated" ? "done":""}`} key={item.id}>
                <div className="check">{item.status === "demonstrated" ? <Check size={15}/> : <span/>}</div>
                <span>{item.label}</span>
              </div>
            ))}
          </div>

          {complete && (
            <div className="complete-card">
              <div className="complete-icon"><Check size={19}/></div>
              <div>
                <strong>Understanding demonstrated</strong>
                <p>The same learning objective was reached through a different path.</p>
              </div>
            </div>
          )}

          <div className="objective">
            <span>LEARNING OBJECTIVE</span>
            <p>Explain why Earth's axial tilt causes the seasons.</p>
          </div>
        </aside>
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
