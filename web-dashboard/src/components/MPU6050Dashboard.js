

import React, { useState, useEffect, useRef } from "react";

function MPU6050Dashboard() {
  const [gesture, setGesture] = useState("WAITING");
  const [aiSentence, setAiSentence] = useState("");
  const [audioEnabled, setAudioEnabled] = useState(false);

  // REFS prevent the "looping" behavior
  const lastSpokenRef = useRef("");
  const isLockedRef = useRef(false);

  // 1. Fetching Data
  useEffect(() => {
    const interval = setInterval(() => {
      fetch("http://localhost:8000/sensors")
        .then(res => res.json())
        .then(data => {
          if (data.gesture !== gesture) setGesture(data.gesture || "WAITING");
          setAiSentence(data.ai_sentence || "");
        });
    }, 200); // Polling every 200ms
    return () => clearInterval(interval);
  }, [gesture]);

  // 2. The "Emergency Stop" Logic
  useEffect(() => {
    if (!audioEnabled) {
      // Tell backend to kill the audio process immediately
      fetch("http://localhost:8000/speak/stop", { method: "POST" });
      lastSpokenRef.current = "";
    }
  }, [audioEnabled]);

  // 3. Strict TTS Trigger
  useEffect(() => {
    // Stop if muted, waiting, or if we just spoke this word
    if (!audioEnabled || gesture === "WAITING" || gesture === lastSpokenRef.current) return;

    // Stop if we are in the 3-second cooldown
    if (isLockedRef.current) return;

    // Trigger Speech
    isLockedRef.current = true;
    lastSpokenRef.current = gesture;

    fetch(`http://localhost:8000/speak/server?text=${encodeURIComponent(gesture)}`)
      .finally(() => {
        // Wait 3 seconds before allowing the NEXT word to be spoken
        // This stops the "Hello... Hello... Hello" repetition
        setTimeout(() => {
          isLockedRef.current = false;
        }, 3000);
      });

  }, [gesture, audioEnabled]);

  return (
    <div style={{ background: "#000", minHeight: "100vh", color: "#fff", padding: "40px" }}>
      <div style={{ maxWidth: "600px", margin: "0 auto", border: "1px solid #333", padding: "20px", borderRadius: "20px" }}>

        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "30px" }}>
          <h2>SignSpeak</h2>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span>{audioEnabled ? "🔊 ON" : "🔇 OFF"}</span>
            <input
              type="checkbox"
              checked={audioEnabled}
              onChange={() => setAudioEnabled(!audioEnabled)}
              style={{ width: "25px", height: "25px" }}
            />
          </div>
        </div>

        <div style={{ textAlign: "center", padding: "50px 0", background: "#111", borderRadius: "15px" }}>
          <p style={{ opacity: 0.5, fontSize: "12px" }}>GESTURE</p>
          <h1 style={{ fontSize: "80px", color: "#e6d58c", margin: 0 }}>{gesture}</h1>
        </div>

        <div style={{ marginTop: "20px", padding: "20px", background: "#1a1a1a", borderRadius: "10px" }}>
          <p style={{ color: "#888", fontSize: "12px", margin: "0 0 10px 0" }}>AI SENTENCE</p>
          <p style={{ fontSize: "20px", margin: 0 }}>{aiSentence || "Waiting..."}</p>
        </div>

      </div>
    </div>
  );
}

export default MPU6050Dashboard;