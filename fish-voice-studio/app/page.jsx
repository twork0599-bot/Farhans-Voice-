"use client";

import { useEffect, useRef, useState } from "react";

const STORE_KEY = "farhan-fish-voice-settings-v1";

export default function Home() {
  const [text, setText] = useState("");
  const [voiceId, setVoiceId] = useState("");
  const [voiceName, setVoiceName] = useState("");
  const [voices, setVoices] = useState([]);
  const [speed, setSpeed] = useState(1);
  const [model, setModel] = useState("s2.1-pro");
  const [audioUrl, setAudioUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const audioRef = useRef(null);

  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(STORE_KEY) || "{}");
      setVoices(Array.isArray(saved.voices) ? saved.voices : []);
      setVoiceId(saved.voiceId || "");
      setSpeed(typeof saved.speed === "number" ? saved.speed : 1);
      setModel(saved.model || "s2.1-pro");
    } catch {}
  }, []);

  useEffect(() => {
    localStorage.setItem(STORE_KEY, JSON.stringify({ voices, voiceId, speed, model }));
  }, [voices, voiceId, speed, model]);

  useEffect(() => () => { if (audioUrl) URL.revokeObjectURL(audioUrl); }, [audioUrl]);

  function saveVoice() {
    const id = voiceId.trim();
    const name = voiceName.trim() || "My voice";
    if (!id) return setError("Enter a Voice ID first.");
    setError("");
    setVoices((old) => [{ id, name }, ...old.filter((v) => v.id !== id)]);
    setVoiceName("");
    setStatus("Voice ID saved on this device.");
  }

  function removeVoice(id) {
    setVoices((old) => old.filter((v) => v.id !== id));
    if (voiceId === id) setVoiceId("");
  }

  async function generate() {
    setError("");
    setStatus("");
    if (!text.trim()) return setError("Write something first.");
    if (!voiceId.trim()) return setError("Enter or select a Voice ID.");
    setBusy(true);
    try {
      const response = await fetch("/api/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, referenceId: voiceId.trim(), speed, model }),
      });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.error || "Could not generate audio.");
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setAudioUrl((old) => { if (old) URL.revokeObjectURL(old); return url; });
      setStatus("Your MP3 is ready.");
    } catch (e) {
      setError(e.message || "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <a className="brand" href="#"><span className="brandmark">F</span><span>FARHAN <b>VOICE STUDIO</b></span></a>
        <span className="powered">POWERED BY FISH AUDIO</span>
      </header>

      <section className="hero">
        <div className="eyebrow"><span className="pulse" /> TEXT TO SPEECH STUDIO</div>
        <h1>Give your words<br /><em>a voice.</em></h1>
        <p>Generate natural speech with your saved Fish Audio voices. Adjust the pace and download your audio as MP3.</p>
      </section>

      <section className="workspace">
        <div className="panel mainpanel">
          <div className="panelhead"><div><span className="step">01</span><h2>Your script</h2></div><span className="counter">{text.length.toLocaleString()} / 5,000</span></div>
          <textarea value={text} maxLength={5000} onChange={(e) => setText(e.target.value)} placeholder="Type or paste the words you want to turn into speech..." />
          <div className="panelhead voicehead"><div><span className="step">02</span><h2>Choose a voice</h2></div></div>
          <div className="voicegrid">
            <div className="field"><label>VOICE ID</label><input value={voiceId} onChange={(e) => setVoiceId(e.target.value)} placeholder="Paste your Fish Audio Voice ID" /></div>
            <div className="field"><label>SAVED VOICES</label><select value={voices.some(v => v.id === voiceId) ? voiceId : ""} onChange={(e) => setVoiceId(e.target.value)}><option value="">Choose saved voice</option>{voices.map(v => <option key={v.id} value={v.id}>{v.name} · {v.id.slice(0,8)}…</option>)}</select></div>
          </div>
          <div className="savevoice">
            <input value={voiceName} onChange={(e) => setVoiceName(e.target.value)} placeholder="Voice name (e.g. My Bangla Voice)" />
            <button className="subtlebtn" onClick={saveVoice}>＋ Save Voice ID</button>
          </div>
          {voices.length > 0 && <div className="savedlist">{voices.map(v => <div className="saveditem" key={v.id}><span><b>{v.name}</b><small>{v.id}</small></span><button onClick={() => removeVoice(v.id)} aria-label="Delete voice">×</button></div>)}</div>}
          <div className="panelhead voicehead"><div><span className="step">03</span><h2>Voice settings</h2></div><span className="autosave">● AUTO-SAVED</span></div>
          <div className="settingsgrid">
            <div className="settingbox">
              <div className="settingtitle"><label>SPEAKING SPEED</label><strong>{speed.toFixed(1)}x</strong></div>
              <input className="range" type="range" min="0.5" max="2" step="0.1" value={speed} onChange={(e) => setSpeed(Number(e.target.value))} />
              <div className="rangeends"><span>0.5x · Slower</span><button onClick={() => setSpeed(1)}>Reset 1.0x</button><span>2.0x · Faster</span></div>
            </div>
            <div className="settingbox"><label>AI MODEL</label><select value={model} onChange={(e) => setModel(e.target.value)}><option value="s2.1-pro">S2.1 Pro · Recommended</option><option value="s2-pro">S2 Pro</option><option value="s2.1-pro-free">S2.1 Pro Free</option></select></div>
          </div>
          <button className="generate" onClick={generate} disabled={busy}>{busy ? <><span className="spinner" /> Generating audio…</> : <>Generate MP3 <span>↗</span></>}</button>
          {error && <p className="message error">{error}</p>}
          {status && <p className="message success">{status}</p>}
        </div>

        <aside className="panel outputpanel">
          <div className="outputicon">♫</div><h2>Your audio</h2><p>Your generated speech will appear here. Listen, then save the MP3 to your device.</p>
          {audioUrl ? <><audio ref={audioRef} controls src={audioUrl} /><a className="download" href={audioUrl} download="farhan-voice.mp3">↓ Download MP3</a></> : <div className="empty"><span>◖)))</span><small>Waiting for your first generation</small></div>}
          <div className="tip"><b>QUICK TIP</b><p>Use 0.8x for a slower, calmer delivery. 1.0x is normal speed. Try 1.2x for a quicker pace.</p></div>
        </aside>
      </section>
      <footer><span>FARHAN VOICE STUDIO</span><span>Voice IDs and settings are saved in this browser only.</span></footer>
    </main>
  );
}
