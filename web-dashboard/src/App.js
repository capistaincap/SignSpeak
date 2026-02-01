import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  // ---------------- STATE ----------------
  const [gesture, setGesture] = useState('WAITING');
  const [sentence, setSentence] = useState('Waiting for gesture...');
  const [language, setLanguage] = useState('en');
  const [deviceStatus, setDeviceStatus] = useState('DISCONNECTED');
  const [latency, setLatency] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const [gestureIcon, setGestureIcon] = useState('fas fa-hand-paper');
  const [useGemini, setUseGemini] = useState(true);
  const [logs, setLogs] = useState([]);
  const [backendIP, setBackendIP] = useState(localStorage.getItem('backendIP') || 'localhost');
  const [autoSpeak, setAutoSpeak] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard'); // dashboard, analytics, history, settings
  const [isSystemOn, setIsSystemOn] = useState(true);

  const autoSpeakRef = useRef(autoSpeak);
  const lastSpokenGesture = useRef(null);

  useEffect(() => {
    localStorage.setItem('backendIP', backendIP);
  }, [backendIP]);

  useEffect(() => {
    autoSpeakRef.current = autoSpeak;
  }, [autoSpeak]);

  const addLog = (message) => {
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setLogs(prev => [{ time: timestamp, message, id: Date.now() }, ...prev].slice(0, 50));
  };

  // ---------------- BACKEND POLLING ----------------
  const BACKEND_URL = `http://${backendIP}:8000/sensors`;

  useEffect(() => {
    let isMounted = true;
    const controller = new AbortController();
    const { signal } = controller;

    const pollInterval = setInterval(() => {
      if (!isSystemOn) return;
      const startTime = performance.now();

      fetch(`${BACKEND_URL}?use_gemini=${useGemini}&lang=${language}&auto_speak=${autoSpeak}`, { signal })
        .then(res => {
          if (!res.ok) throw new Error('Network response was not ok');
          return res.json();
        })
        .then(data => {
          if (!isMounted) return;
          const endTime = performance.now();
          setLatency(Math.round(endTime - startTime));

          if (!isConnected) {
            setIsConnected(true);
            setDeviceStatus('CONNECTED');
            addLog(`Connected: ${latency}ms`);
          }

          const g = data.gesture || 'WAITING';
          if (g !== 'WAITING' && g !== gesture) {
            setGesture(g);
            addLog(`Detected: ${g}`);

            // Icon Map
            const icons = {
              HELLO: 'fas fa-hand-peace',
              YES: 'fas fa-thumbs-up',
              NO: 'fas fa-thumbs-down',
              STOP: 'fas fa-hand-paper'
            };
            setGestureIcon(icons[g] || 'fas fa-hand-paper');
          }

          // Always update sentence if it changes (Decoupled from gesture)
          if (data.sentence && data.sentence !== sentence) {
            setSentence(data.sentence);
            if (autoSpeakRef.current && data.sentence !== 'Processing...' && data.sentence !== 'Waiting for gesture...') {
              speakSentence(data.sentence);
            }
          }
          if (g === 'WAITING') {
            setGesture('WAITING');
            lastSpokenGesture.current = null;
          }
        })
        .catch((e) => {
          if (!isMounted || e.name === 'AbortError') return;
          // Only disconnect if it's a real error and we were connected
          // To prevent flickering, maybe we should have a retry count?
          // For now, let's just log it and NOT aggressively disconnect on single failure
          console.warn("Polling error:", e);
          // if (isConnected) setIsConnected(false); // DISABLED aggressive disconnect
        });
    }, 100);

    return () => {
      isMounted = false;
      controller.abort();
      clearInterval(pollInterval);
    };
  }, [useGemini, gesture, backendIP, language, isSystemOn]);

  // ---------------- TTS ----------------
  const speakSentence = async (text) => {
    if (!text || text === 'Waiting for gesture...') return;

    try {
      // Use Server-Side Playback (Robust)
      const audioUrl = `http://${backendIP}:8000/audio/speak/server?text=${encodeURIComponent(text)}`;
      await fetch(audioUrl);
    } catch (e) {
      console.warn("Backend TTS failed:", e);
    }
  };

  // ---------------- RENDER ----------------
  return (
    <div className="app-container">

      {/* SIDEBAR */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo-icon">S</div>
          <h3>SignSpeak</h3>
        </div>

        <nav className="sidebar-nav">
          <button className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveTab('dashboard')}>
            <i className="fas fa-home"></i> <span>Dashboard</span>
          </button>
          <button className={`nav-item ${activeTab === 'analytics' ? 'active' : ''}`} onClick={() => setActiveTab('analytics')}>
            <i className="fas fa-chart-bar"></i> <span>Analytics</span>
          </button>
          <button className={`nav-item ${activeTab === 'history' ? 'active' : ''}`} onClick={() => setActiveTab('history')}>
            <i className="fas fa-history"></i> <span>History</span>
          </button>
          <button className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`} onClick={() => setActiveTab('settings')}>
            <i className="fas fa-cog"></i> <span>Settings</span>
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className={`connection-status ${isConnected ? 'online' : 'offline'}`}>
            <div className="status-dot"></div>
            <span>{isConnected ? 'Online' : 'Offline'}</span>
          </div>
          <div className="power-toggle">
            <span>System</span>
            <div
              className={`power-btn-mini ${isSystemOn ? 'on' : 'off'}`}
              onClick={() => setIsSystemOn(!isSystemOn)}
            >
              <i className="fas fa-power-off"></i>
            </div>
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <main className="main-content">

        {/* HEADER */}
        <header className="top-header">
          <h2>{activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}</h2>
          <div className="header-actions">
            <button onClick={() => setIsConnected(true)} className="btn-connect-sm">
              {isConnected ? 'Connected' : 'Connect Glove'}
            </button>
            <div className="profile-avatar">S</div>
          </div>
        </header>

        <div className="content-scrollable">

          {/* --- TAB: DASHBOARD --- */}
          {activeTab === 'dashboard' && (
            <div className="dashboard-grid">

              {/* LIVE GESTURE CARD (Span 2 cols) */}
              <div className="card card-hero">
                <div className="card-title">
                  <span>Live Gesture Recognition</span>
                  <i className="fas fa-broadcast-tower" style={{ color: '#E6D48F' }}></i>
                </div>
                <div className="hero-content">
                  <div className="hero-text">
                    {!isSystemOn ? 'PAUSED' : (gesture === 'WAITING' ? '...' : gesture)}
                  </div>
                  <div className="gesture-meta">
                    <div className="confidence-badge">
                      {!isSystemOn ? 'System Offline' : `Confidence: ${gesture === 'WAITING' ? '0%' : '94%'}`}
                    </div>
                    <div className="status-chip">
                      <i className="fas fa-circle" style={{ fontSize: 8 }}></i> Stable
                    </div>
                  </div>
                </div>
              </div>

              {/* AI SENTENCE CARD (Span 2 cols) */}
              <div className="card card-ai">
                <div className="card-title">
                  <span style={{ color: 'white' }}>AI Sentence</span>
                  <div className="card-actions">
                    <i className="fas fa-sync-alt" onClick={() => { setSentence('Waiting for gesture...'); setGesture('WAITING'); }}></i>
                    <i className="fas fa-brain" style={{ color: '#BEE8D0' }}></i>
                  </div>
                </div>
                <div className="ai-text">
                  "{sentence}"
                </div>
                <div className="ai-footer">
                  <div className="ai-tag">
                    <i className="fas fa-sparkles"></i> Powered by Gemini
                  </div>
                  <button className="btn-icon" onClick={() => speakSentence(sentence)}>
                    <i className="fas fa-volume-up"></i>
                  </button>
                </div>
              </div>

              {/* CONTROLS ROW (Span 1 col each) */}
              <div className="card card-stat clickable" onClick={() => setAutoSpeak(!autoSpeak)}>
                <div className="stat-icon"><i className="fas fa-volume-up"></i></div>
                <div className="stat-info">
                  <span className="stat-label">Audio Output</span>
                  <span className={`stat-value ${autoSpeak ? 'on' : 'off'}`}>{autoSpeak ? 'ON' : 'OFF'}</span>
                </div>
              </div>

              <div className="card card-stat clickable" onClick={() => setUseGemini(!useGemini)}>
                <div className="stat-icon"><i className="fas fa-magic"></i></div>
                <div className="stat-info">
                  <span className="stat-label">Speak Sentence</span>
                  <span className={`stat-value ${useGemini ? 'on' : 'off'}`}>{useGemini ? 'ON' : 'OFF'}</span>
                </div>
              </div>

              <div className="card card-stat">
                <div className="stat-icon"><i className="fas fa-language"></i></div>
                <div className="stat-info">
                  <span className="stat-label">Target Lang</span>
                  <span className="stat-value">{language.toUpperCase()}</span>
                </div>
              </div>

              <div className="card card-stat">
                <div className="stat-icon"><i className="fas fa-bolt"></i></div>
                <div className="stat-info">
                  <span className="stat-label">Latency</span>
                  <span className="stat-value highlight">{latency}ms</span>
                </div>
              </div>

            </div>
          )}

          {/* --- TAB: ANALYTICS --- */}
          {activeTab === 'analytics' && (
            <div className="tab-content">
              <div className="card">
                <div className="card-title">Gesture Accuracy</div>
                <div className="chart-container">
                  {[40, 70, 50, 90, 60, 80, 95].map((h, i) => (
                    <div key={i} className="bar" style={{ height: h + '%' }}>
                      <div className="bar-fill" style={{ height: '100%', opacity: i === 6 ? 1 : 0.4 }}></div>
                    </div>
                  ))}
                </div>
                <div style={{ textAlign: 'center', marginTop: 10, color: '#9CA3AF', fontSize: '0.8rem' }}>Last 7 Sessions</div>
              </div>

              <div className="card">
                <div className="card-title">Session Summary</div>
                <div className="setting-row">
                  <span style={{ color: '#9CA3AF' }}>Total Gestures</span>
                  <span style={{ color: 'white', fontWeight: 'bold' }}>1,240</span>
                </div>
                <div className="setting-row">
                  <span style={{ color: '#9CA3AF' }}>Sentences</span>
                  <span style={{ color: 'white', fontWeight: 'bold' }}>85</span>
                </div>
                <div className="setting-row">
                  <span style={{ color: '#9CA3AF' }}>Avg Accuracy</span>
                  <span style={{ color: '#E6D48F', fontWeight: 'bold' }}>92%</span>
                </div>
              </div>
            </div>
          )}

          {/* --- TAB: HISTORY --- */}
          {activeTab === 'history' && (
            <div className="tab-content">
              {logs.length === 0 && <div className="empty-state">No recent activity</div>}
              {logs.map(log => (
                <div key={log.id} className="card history-item">
                  <div className="log-content">
                    <span className="log-msg">{log.message}</span>
                    <span className="log-time">{log.time}</span>
                  </div>
                  <i className="fas fa-check-circle success-icon"></i>
                </div>
              ))}
            </div>
          )}

          {/* --- TAB: SETTINGS --- */}
          {activeTab === 'settings' && (
            <div className="tab-content settings-container">
              <div className="card">
                <div className="card-title">General Preferences</div>
                {/* Language Select Reposted Here */}
                <div className="setting-row">
                  <span>Target Language</span>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="desktop-select"
                  >
                    <option value="en">English (US)</option>
                    <option value="hi">Hindi (हिंदी)</option>
                    <option value="mr">Marathi (मराठी)</option>
                    <option value="bn">Bengali (বাংলা)</option>
                    <option value="gu">Gujarati (ગુજરાતી)</option>
                    <option value="ta">Tamil (தமிழ்)</option>
                    <option value="te">Telugu (తెలుగు)</option>
                    <option value="es">Spanish (Español)</option>
                    <option value="fr">French (Français)</option>
                    <option value="de">German (Deutsch)</option>
                    <option value="zh">Chinese (Mandarin)</option>
                    <option value="ja">Japanese (Nihongo)</option>
                    <option value="ko">Korean (Hangul)</option>
                    <option value="ar">Arabic (Al-Arabiyya)</option>
                  </select>
                </div>
              </div>
              <div className="card">
                <div className="card-title">Device Settings</div>
                <div className="setting-row">
                  <span>Backend IP</span>
                  <input
                    className="desktop-input"
                    value={backendIP}
                    onChange={(e) => setBackendIP(e.target.value)}
                  />
                </div>
              </div>
            </div>
          )}

        </div>
      </main>

      {/* CONNECTION OVERLAY - OPTIONAL FOR DESKTOP (Can be a constrained modal) */}
      {!isConnected && (
        <div className="connection-modal-backdrop">
          <div className="connection-modal">
            <i className="fas fa-wifi" style={{ fontSize: '3rem', color: '#E6D48F', marginBottom: 20 }}></i>
            <h2>SignSpeak</h2>
            <p>Connect to your smart glove</p>

            <input
              className="overlay-input"
              value={backendIP}
              onChange={(e) => setBackendIP(e.target.value)}
              placeholder="IP Address (e.g. 192.168.1.5)"
            />

            <button className="btn-primary" onClick={() => setIsConnected(true)}>
              Connect Scanner
            </button>
            <button className="btn-text" onClick={() => setIsConnected(true)}>
              Enter Demo Mode
            </button>
          </div>
        </div>
      )}

    </div>
  );
}

export default App;
