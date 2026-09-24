"""Browser-native real-time video call component for Lingglot.

The component uses Streamlit Components V2 so the live camera preview, Web
Speech API interim transcript, and browser text-to-speech all stay in the
browser. Only finalized learner utterances are sent to Python for the existing
Lingglot learning engine to process.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import streamlit as st


REALTIME_CALL_HTML = r"""
<div class="rtc-shell" aria-label="Lingglot real-time AI language call">
  <header class="rtc-header">
    <div class="rtc-brand-block">
      <span class="rtc-live-pill" id="call-status-pill"><i></i><span id="call-status-text">READY</span></span>
      <div>
        <strong id="character-call-name">Live call</strong>
        <span id="lesson-label">Language practice</span>
        <span class="voice-provider" id="voice-provider">Browser voice</span>
      </div>
    </div>
    <div class="rtc-timer" aria-label="Call duration"><span class="timer-dot"></span><span id="call-timer">00:00</span></div>
  </header>

  <main class="rtc-stage-grid">
    <section class="rtc-tile ai-tile" id="ai-tile" aria-label="Luna AI partner video tile">
      <div class="tile-topline">
        <span class="participant-name" id="ai-participant-name">AI tutor</span>
        <span class="tile-state" id="ai-state">Ready</span>
      </div>
      <div class="ai-orbit orbit-a"></div>
      <div class="ai-orbit orbit-b"></div>
      <div class="ai-avatar-wrap">
        <div class="avatar-halo"></div>
        <img id="luna-avatar" alt="Luna, AI language-learning character" />
        <div class="speaking-ring ring-a"></div>
        <div class="speaking-ring ring-b"></div>
      </div>
      <div class="ai-caption" aria-live="polite">
        <small>Luna says</small>
        <p id="latest-ai-reply" dir="auto">Start the call and say a sentence.</p>
      </div>
      <div class="voice-wave" id="voice-wave" aria-hidden="true">
        <span></span><span></span><span></span><span></span><span></span><span></span>
        <span></span><span></span><span></span><span></span><span></span><span></span>
      </div>
      <button class="soft-action replay-action" id="replay-ai" type="button">🔊 Replay Luna</button>
    </section>

    <section class="rtc-tile user-tile" aria-label="Learner live camera tile">
      <video id="local-video" autoplay muted playsinline></video>
      <div class="camera-placeholder" id="camera-placeholder">
        <div class="camera-icon">◉</div>
        <strong>Your live camera</strong>
        <span>Press Start call and allow camera + microphone access.</span>
      </div>
      <div class="tile-topline user-topline">
        <span class="participant-name">You · learner</span>
        <span class="tile-state" id="media-state">Camera off</span>
      </div>
      <div class="video-footer-overlay">
        <span id="mic-level-label">Mic ready</span>
        <div class="mini-level" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></div>
      </div>
    </section>
  </main>

  <nav class="rtc-controls" aria-label="Video call controls">
    <button id="start-call" class="call-control primary-control" type="button">
      <span class="control-icon">▶</span><span class="control-label">Start call</span>
    </button>
    <button id="toggle-mic" class="call-control" type="button" disabled>
      <span class="control-icon">🎙</span><span class="control-label">Mute</span>
    </button>
    <button id="toggle-camera" class="call-control" type="button" disabled>
      <span class="control-icon">📹</span><span class="control-label">Camera</span>
    </button>
    <button id="toggle-transcript" class="call-control" type="button" disabled>
      <span class="control-icon">◉</span><span class="control-label">Pause transcript</span>
    </button>
  </nav>

  <section class="rtc-status-banner" id="status-banner" data-kind="idle" role="status" aria-live="polite">
    <span class="status-dot"></span>
    <span id="status-message">Ready. Start the call to enable live video and speech recognition.</span>
  </section>

  <section class="rtc-transcript-layout">
    <div class="transcript-card">
      <div class="card-heading-row">
        <div>
          <span class="section-kicker">LIVE TRANSCRIPT</span>
          <h3>Sentence-by-sentence conversation</h3>
        </div>
        <span class="recognition-badge" id="recognition-badge">Checking browser…</span>
      </div>

      <div class="interim-box" id="interim-box">
        <span class="interim-label">Listening now</span>
        <p id="interim-text" dir="auto">Your words will appear here while you speak.</p>
      </div>

      <div class="transcript-history" id="transcript-history" aria-live="polite"></div>
    </div>

    <aside class="manual-card call-info-card">
      <span class="section-kicker">AUTOMATIC PROCESSING</span>
      <h3>Speak naturally</h3>
      <p class="manual-help">Every finalized sentence is sent to Luna automatically. No review or typing step is required.</p>
      <div class="auto-processing-list">
        <div><b>1</b><span>Speak in your selected learning language.</span></div>
        <div><b>2</b><span>Live transcript appears while you talk.</span></div>
        <div><b>3</b><span>Luna replies in that same target language.</span></div>
      </div>
      <div class="compatibility-note" id="compatibility-note">Chrome or Edge is recommended for continuous live transcription.</div>
    </aside>
  </section>
</div>
"""


REALTIME_CALL_CSS = r"""
:host {
  display: block;
  width: 100%;
  height: 100%;
  color: #3b2020;
  font-family: var(--st-font, "Plus Jakarta Sans", system-ui, sans-serif);
}

* { box-sizing: border-box; }
button, textarea, input { font: inherit; }

.rtc-shell {
  width: 100%;
  height: 100%;
  overflow: auto;
  padding: 18px;
  border: 1px solid rgba(235, 198, 181, 0.86);
  border-radius: 30px;
  background:
    radial-gradient(circle at 12% 4%, rgba(255, 148, 116, .22), transparent 30%),
    radial-gradient(circle at 92% 12%, rgba(255, 91, 167, .18), transparent 26%),
    linear-gradient(145deg, rgba(255, 252, 246, .98), rgba(255, 244, 235, .96));
  box-shadow: 0 24px 70px -38px rgba(88, 36, 28, .52);
}

.rtc-header,
.rtc-brand-block,
.rtc-controls,
.card-heading-row,
.manual-actions,
.tile-topline,
.video-footer-overlay {
  display: flex;
  align-items: center;
}

.rtc-header { justify-content: space-between; gap: 16px; margin-bottom: 14px; }
.rtc-brand-block { gap: 12px; min-width: 0; }
.rtc-brand-block strong { display: block; font-family: var(--st-heading-font, Georgia, serif); font-size: 1.22rem; }
.rtc-brand-block > div span { display: block; margin-top: 2px; color: #8a6961; font-size: .8rem; }
.voice-provider { display: inline-block !important; width: fit-content; margin-top: 5px !important; padding: 3px 7px; border-radius: 999px; background: #fff0f7; color: #a33e72 !important; font-size: .6rem !important; font-weight: 800; }

.rtc-live-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 7px 11px;
  border: 1px solid #efd8cc;
  border-radius: 999px;
  background: rgba(255,255,255,.82);
  color: #8b6d65;
  font-size: .72rem;
  font-weight: 800;
  letter-spacing: .08em;
}
.rtc-live-pill i,
.status-dot,
.timer-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #c7aaa0;
}
.rtc-live-pill.is-live { color: #d83d5f; border-color: rgba(255,83,116,.4); }
.rtc-live-pill.is-live i { background: #ff496c; box-shadow: 0 0 0 0 rgba(255,73,108,.5); animation: pulse-live 1.5s infinite; }

.rtc-timer {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 78px;
  justify-content: center;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255,255,255,.78);
  border: 1px solid #efd8cc;
  color: #6d4b45;
  font-variant-numeric: tabular-nums;
  font-weight: 700;
}
.rtc-timer .timer-dot { background: #ff6a4d; }

.rtc-stage-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(300px, .92fr);
  gap: 14px;
}

.rtc-tile {
  position: relative;
  min-height: 365px;
  overflow: hidden;
  border: 1px solid rgba(235, 196, 178, .9);
  border-radius: 25px;
  background: #fffaf5;
  box-shadow: 0 18px 45px -32px rgba(76, 28, 23, .65);
}

.ai-tile {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 55px 22px 18px;
  background:
    radial-gradient(circle at 50% 48%, rgba(255, 164, 127, .28), transparent 34%),
    radial-gradient(circle at 18% 15%, rgba(255, 210, 188, .7), transparent 25%),
    radial-gradient(circle at 88% 82%, rgba(255, 183, 220, .52), transparent 29%),
    linear-gradient(145deg, #fff6ea, #fffaf5 48%, #fff0f8);
}

.user-tile { background: #261d22; }
#local-video {
  width: 100%;
  height: 100%;
  min-height: 365px;
  display: none;
  object-fit: cover;
  transform: scaleX(-1);
  background: #1e171b;
}
#local-video.is-live { display: block; }

.camera-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 30px;
  text-align: center;
  color: #f8e9e2;
  background:
    radial-gradient(circle at 50% 45%, rgba(255, 105, 83, .2), transparent 30%),
    linear-gradient(145deg, #2c2025, #171115);
}
.camera-placeholder.hidden { display: none; }
.camera-placeholder .camera-icon {
  width: 62px;
  height: 62px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  color: white;
  font-size: 1.6rem;
  background: linear-gradient(135deg, #ff714d, #ff4f9a);
  box-shadow: 0 14px 40px -20px rgba(255,79,154,.9);
}
.camera-placeholder span { max-width: 300px; color: #cbb5ae; font-size: .82rem; line-height: 1.5; }

.tile-topline {
  position: absolute;
  z-index: 8;
  top: 14px;
  left: 14px;
  right: 14px;
  justify-content: space-between;
  gap: 10px;
}
.participant-name,
.tile-state {
  padding: 6px 10px;
  border: 1px solid rgba(255,255,255,.46);
  border-radius: 999px;
  background: rgba(255,255,255,.76);
  backdrop-filter: blur(10px);
  font-size: .72rem;
  font-weight: 750;
  color: #573a35;
}
.user-topline .participant-name,
.user-topline .tile-state {
  border-color: rgba(255,255,255,.18);
  background: rgba(22,14,18,.55);
  color: white;
}

.ai-avatar-wrap { position: relative; width: 205px; height: 205px; display: grid; place-items: center; }
#luna-avatar { position: relative; z-index: 4; width: 178px; height: 178px; filter: drop-shadow(0 18px 24px rgba(99,42,33,.18)); animation: avatar-breathe 4s ease-in-out infinite; }
.avatar-halo { position: absolute; inset: 8px; border-radius: 50%; background: radial-gradient(circle, rgba(255,255,255,.96), rgba(255,166,133,.26) 53%, transparent 72%); }
.speaking-ring { position: absolute; inset: 8px; border: 2px solid rgba(255,91,132,.32); border-radius: 50%; opacity: 0; }
.ai-tile.is-speaking .speaking-ring { animation: speaking-ring 1.5s ease-out infinite; }
.ai-tile.is-speaking .ring-b { animation-delay: .55s; }
.ai-tile.is-thinking #luna-avatar { animation: thinking-float 1.15s ease-in-out infinite; }

.ai-orbit { position: absolute; border: 1px dashed rgba(255,108,95,.22); border-radius: 50%; pointer-events: none; }
.orbit-a { width: 320px; height: 320px; animation: orbit-spin 18s linear infinite; }
.orbit-b { width: 270px; height: 270px; animation: orbit-spin 13s linear infinite reverse; }

.ai-caption {
  position: relative;
  z-index: 5;
  width: min(92%, 620px);
  margin-top: 4px;
  padding: 12px 15px;
  border: 1px solid rgba(238, 198, 183, .86);
  border-radius: 17px;
  background: rgba(255,255,255,.79);
  backdrop-filter: blur(10px);
  text-align: center;
}
.ai-caption small { display: block; color: #aa7d70; font-size: .68rem; font-weight: 800; letter-spacing: .06em; text-transform: uppercase; }
.ai-caption p { margin: 4px 0 0; color: #432522; font-size: .93rem; line-height: 1.48; }
.voice-wave { position: relative; z-index: 5; height: 22px; display: flex; align-items: center; gap: 3px; margin-top: 8px; }
.voice-wave span { width: 3px; height: 5px; border-radius: 999px; background: linear-gradient(#ff714f, #ff4f9e); opacity: .4; }
.ai-tile.is-speaking .voice-wave span { animation: wave 760ms ease-in-out infinite alternate; opacity: .95; }
.ai-tile.is-speaking .voice-wave span:nth-child(2n) { animation-delay: .13s; }
.ai-tile.is-speaking .voice-wave span:nth-child(3n) { animation-delay: .26s; }
.replay-action { position: relative; z-index: 5; margin-top: 6px; }

.video-footer-overlay {
  position: absolute;
  z-index: 8;
  left: 14px;
  right: 14px;
  bottom: 14px;
  justify-content: space-between;
  padding: 8px 11px;
  border: 1px solid rgba(255,255,255,.16);
  border-radius: 14px;
  background: rgba(20,13,17,.54);
  backdrop-filter: blur(10px);
  color: white;
  font-size: .75rem;
}
.mini-level { display: flex; align-items: flex-end; gap: 2px; height: 15px; }
.mini-level i { display: block; width: 3px; height: 4px; border-radius: 3px; background: #ff8060; }
.user-tile.is-live .mini-level i { animation: mic-level 900ms ease-in-out infinite alternate; }
.user-tile.is-live .mini-level i:nth-child(2) { animation-delay: .15s; }
.user-tile.is-live .mini-level i:nth-child(3) { animation-delay: .3s; }
.user-tile.is-live .mini-level i:nth-child(4) { animation-delay: .45s; }
.user-tile.is-live .mini-level i:nth-child(5) { animation-delay: .6s; }

.rtc-controls { justify-content: center; flex-wrap: wrap; gap: 10px; padding: 14px 4px 8px; }
.call-control,
.soft-action,
  border: 1px solid #ead3c8;
  border-radius: 999px;
  background: rgba(255,255,255,.9);
  color: #51332e;
  cursor: pointer;
  transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease;
}
.call-control { min-width: 120px; padding: 10px 14px; display: inline-flex; align-items: center; justify-content: center; gap: 7px; }
.call-control:hover:not(:disabled), .soft-action:hover { transform: translateY(-1px); border-color: #ff9074; box-shadow: 0 10px 22px -16px rgba(91,34,27,.7); }
.call-control:disabled { cursor: not-allowed; opacity: .46; }
.primary-control { color: white; border-color: transparent; background: linear-gradient(125deg, #ff704c, #ff4d94 58%, #ee55c8); }
.primary-control.is-ending { background: linear-gradient(125deg, #e13f56, #bd234f); }
.control-icon { font-size: .92rem; }
.control-label { font-size: .76rem; font-weight: 800; }
.soft-action { padding: 7px 12px; font-size: .73rem; font-weight: 750; }

.rtc-status-banner {
  display: flex;
  align-items: center;
  gap: 9px;
  min-height: 42px;
  margin: 2px 0 13px;
  padding: 10px 13px;
  border: 1px solid #edd7cc;
  border-radius: 14px;
  background: rgba(255,255,255,.72);
  color: #74554e;
  font-size: .78rem;
}
.rtc-status-banner[data-kind="live"] .status-dot { background: #2cb67d; box-shadow: 0 0 0 4px rgba(44,182,125,.13); }
.rtc-status-banner[data-kind="thinking"] .status-dot { background: #f49b35; box-shadow: 0 0 0 4px rgba(244,155,53,.13); }
.rtc-status-banner[data-kind="speaking"] .status-dot { background: #ff4f95; box-shadow: 0 0 0 4px rgba(255,79,149,.13); }
.rtc-status-banner[data-kind="error"] { color: #9f2f42; border-color: rgba(218,57,83,.34); background: rgba(255,237,240,.8); }
.rtc-status-banner[data-kind="error"] .status-dot { background: #da3953; }

.rtc-transcript-layout { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(270px, .65fr); gap: 13px; }
.transcript-card,
.manual-card {
  min-width: 0;
  padding: 16px;
  border: 1px solid rgba(235, 198, 181, .88);
  border-radius: 22px;
  background: rgba(255,255,255,.78);
}
.card-heading-row { justify-content: space-between; gap: 12px; }
.section-kicker { display: block; color: #dd5d63; font-size: .66rem; font-weight: 850; letter-spacing: .1em; }
.transcript-card h3,
.manual-card h3 { margin: 3px 0 0; font-family: var(--st-heading-font, Georgia, serif); font-size: 1.04rem; }
.recognition-badge { padding: 6px 9px; border-radius: 999px; background: #fff1e8; color: #9a6658; font-size: .67rem; font-weight: 750; white-space: nowrap; }
.recognition-badge.supported { color: #187a58; background: #e8f8f1; }
.recognition-badge.unsupported { color: #a23b4e; background: #ffedf1; }

.interim-box { margin-top: 12px; padding: 10px 12px; border: 1px dashed #efc9bb; border-radius: 15px; background: linear-gradient(120deg, rgba(255,244,235,.9), rgba(255,238,247,.74)); }
.interim-label { color: #b06e61; font-size: .67rem; font-weight: 800; text-transform: uppercase; letter-spacing: .07em; }
.interim-box p { min-height: 22px; margin: 4px 0 0; color: #6e4e48; font-size: .86rem; font-style: italic; line-height: 1.45; }
.interim-box.is-listening { border-color: #ff8b71; box-shadow: inset 0 0 0 1px rgba(255,139,113,.12); }

.transcript-history { height: 245px; overflow-y: auto; margin-top: 10px; padding-right: 4px; display: flex; flex-direction: column; gap: 9px; scrollbar-width: thin; }
.transcript-empty { display: grid; place-items: center; height: 100%; color: #a48b83; text-align: center; font-size: .8rem; }
.transcript-bubble { max-width: 88%; padding: 10px 12px; border-radius: 15px; font-size: .83rem; line-height: 1.48; }
.transcript-bubble.user { align-self: flex-end; color: white; border-bottom-right-radius: 5px; background: linear-gradient(125deg, #ff6c4c, #ff4f94); }
.transcript-bubble.assistant { align-self: flex-start; color: #4b2e29; border: 1px solid #edd6cb; border-bottom-left-radius: 5px; background: #fffaf7; }
.bubble-label { display: block; margin-bottom: 3px; font-size: .62rem; font-weight: 850; opacity: .72; text-transform: uppercase; letter-spacing: .06em; }
.bubble-feedback { display: block; margin-top: 6px; padding-top: 6px; border-top: 1px solid rgba(98,57,49,.12); font-size: .7rem; opacity: .82; }
.bubble-points { display: inline-block; margin-top: 6px; padding: 3px 7px; border-radius: 999px; background: rgba(255,255,255,.6); font-size: .64rem; font-weight: 800; }

.manual-help { margin: 7px 0 11px; color: #80645d; font-size: .76rem; line-height: 1.5; }
.manual-actions { justify-content: space-between; gap: 8px; margin-top: 9px; }
.autosend-label { display: inline-flex; align-items: center; gap: 6px; color: #75564f; font-size: .7rem; cursor: pointer; }
.autosend-label input { accent-color: #ff5d70; }
.compatibility-note { margin-top: 11px; padding: 9px 10px; border-radius: 12px; background: #fff3e9; color: #8d6257; font-size: .69rem; line-height: 1.45; }
.compatibility-note.error { background: #ffedf0; color: #9d3148; }
.call-tips { margin: 11px 0 0; padding-left: 18px; color: #7f635c; font-size: .7rem; line-height: 1.55; }

@keyframes pulse-live { 70% { box-shadow: 0 0 0 7px rgba(255,73,108,0); } 100% { box-shadow: 0 0 0 0 rgba(255,73,108,0); } }
@keyframes avatar-breathe { 0%,100% { transform: translateY(0) scale(1); } 50% { transform: translateY(-5px) scale(1.015); } }
@keyframes thinking-float { 0%,100% { transform: translateY(0) rotate(-1deg); } 50% { transform: translateY(-8px) rotate(1deg); } }
@keyframes speaking-ring { 0% { transform: scale(.75); opacity: .55; } 100% { transform: scale(1.35); opacity: 0; } }
@keyframes orbit-spin { to { transform: rotate(360deg); } }
@keyframes wave { from { height: 4px; } to { height: 19px; } }
@keyframes mic-level { from { height: 3px; } to { height: 14px; } }


.call-info-card { min-height: 100%; }
.auto-processing-list { display:grid; gap:10px; margin-top:14px; }
.auto-processing-list div { display:flex; align-items:flex-start; gap:10px; padding:10px 12px; border:1px solid #efdacf; border-radius:14px; background:rgba(255,255,255,.68); }
.auto-processing-list b { width:24px; height:24px; display:grid; place-items:center; border-radius:50%; background:#ffe6dc; color:#a14d39; font-size:.75rem; }
.auto-processing-list span { flex:1; color:#73574f; font-size:.78rem; line-height:1.45; }

@media (max-width: 840px) {
  .rtc-stage-grid,
  .rtc-transcript-layout { grid-template-columns: 1fr; }
  .rtc-tile { min-height: 330px; }
  #local-video { min-height: 330px; }
  .transcript-history { height: 220px; }
}

@media (max-width: 560px) {
  .rtc-shell { padding: 11px; border-radius: 22px; }
  .rtc-header { align-items: flex-start; }
  .rtc-brand-block > div span { display: none; }
  .rtc-tile { min-height: 310px; border-radius: 20px; }
  #local-video { min-height: 310px; }
  .ai-avatar-wrap { width: 170px; height: 170px; }
  #luna-avatar { width: 148px; height: 148px; }
  .call-control { min-width: 0; flex: 1 1 42%; }
}
"""


REALTIME_CALL_JS = r"""
export default function(component) {
  const { data, setTriggerValue, parentElement } = component;
  const safeData = data || {};

  let runtime = parentElement.__lingglotRealtimeRuntime;

  function q(selector) {
    return parentElement.querySelector(selector);
  }

  function setStatus(message, kind = "idle") {
    const banner = q("#status-banner");
    const text = q("#status-message");
    if (banner) banner.dataset.kind = kind;
    if (text) text.textContent = message;
  }

  function formatTime(seconds) {
    const mins = Math.floor(seconds / 60).toString().padStart(2, "0");
    const secs = Math.floor(seconds % 60).toString().padStart(2, "0");
    return `${mins}:${secs}`;
  }

  function updateTimer() {
    if (!runtime || !runtime.callActive || !runtime.callStartedAt) return;
    const elapsed = Math.max(0, (Date.now() - runtime.callStartedAt) / 1000);
    q("#call-timer").textContent = formatTime(elapsed);
  }

  function updateControls() {
    const startButton = q("#start-call");
    const micButton = q("#toggle-mic");
    const cameraButton = q("#toggle-camera");
    const transcriptButton = q("#toggle-transcript");
    const livePill = q("#call-status-pill");
    const liveText = q("#call-status-text");
    const userTile = q(".user-tile");

    startButton.classList.toggle("is-ending", runtime.callActive);
    startButton.querySelector(".control-icon").textContent = runtime.callActive ? "■" : "▶";
    startButton.querySelector(".control-label").textContent = runtime.callActive ? "End call" : "Start call";

    micButton.disabled = !runtime.callActive;
    cameraButton.disabled = !runtime.callActive;
    transcriptButton.disabled = !runtime.callActive || !runtime.recognitionSupported;

    micButton.querySelector(".control-icon").textContent = runtime.micMuted ? "🔇" : "🎙";
    micButton.querySelector(".control-label").textContent = runtime.micMuted ? "Unmute" : "Mute";
    cameraButton.querySelector(".control-icon").textContent = runtime.cameraOff ? "🚫" : "📹";
    cameraButton.querySelector(".control-label").textContent = runtime.cameraOff ? "Camera on" : "Camera off";
    transcriptButton.querySelector(".control-icon").textContent = runtime.transcriptPaused ? "▷" : "◉";
    transcriptButton.querySelector(".control-label").textContent = runtime.transcriptPaused ? "Resume transcript" : "Pause transcript";

    livePill.classList.toggle("is-live", runtime.callActive);
    liveText.textContent = runtime.callActive ? "LIVE" : "READY";
    userTile.classList.toggle("is-live", runtime.callActive && !runtime.micMuted);
  }

  function stopTracks() {
    if (!runtime.stream) return;
    runtime.stream.getTracks().forEach((track) => track.stop());
    runtime.stream = null;
  }

  function stopRecognition(abort = true) {
    if (!runtime.recognition) return;
    runtime.suppressRecognitionRestart = true;
    try {
      if (abort) runtime.recognition.abort();
      else runtime.recognition.stop();
    } catch (error) {
      // Recognition may already be stopped.
    }
    runtime.recognitionActive = false;
    q("#interim-box").classList.remove("is-listening");
  }

  function cleanupRuntime() {
    if (!runtime || runtime.cleaned) return;
    runtime.cleaned = true;
    stopRecognition(true);
    stopTracks();
    if (runtime.timerInterval) clearInterval(runtime.timerInterval);
    if (runtime.detachmentInterval) clearInterval(runtime.detachmentInterval);
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    if (runtime.audioElement) {
      try { runtime.audioElement.pause(); runtime.audioElement.src = ""; } catch (_) {}
      runtime.audioElement = null;
    }
  }

  function renderHistory(history) {
    const container = q("#transcript-history");
    if (!container) return;
    const items = Array.isArray(history) ? history : [];
    container.replaceChildren();

    if (!items.length) {
      const empty = document.createElement("div");
      empty.className = "transcript-empty";
      empty.textContent = "Start the call and speak. Finalized sentences and Luna's replies will appear here.";
      container.appendChild(empty);
      return;
    }

    items.slice(-30).forEach((message) => {
      const bubble = document.createElement("div");
      const role = message?.role === "user" ? "user" : "assistant";
      bubble.className = `transcript-bubble ${role}`;
      bubble.dir = "auto";

      const label = document.createElement("span");
      label.className = "bubble-label";
      label.textContent = role === "user" ? "You" : (runtime.targetCharacter || "AI tutor");
      bubble.appendChild(label);

      const content = document.createElement("span");
      content.textContent = String(message?.content ?? "");
      bubble.appendChild(content);

      if (role === "assistant" && message?.feedback) {
        const feedback = document.createElement("span");
        feedback.className = "bubble-feedback";
        feedback.textContent = `Tutor feedback: ${message.feedback}`;
        bubble.appendChild(feedback);
      }

      if (role === "assistant" && Number.isFinite(Number(message?.points))) {
        const points = document.createElement("span");
        points.className = "bubble-points";
        points.textContent = `+${Number(message.points)} points`;
        bubble.appendChild(points);
      }

      container.appendChild(bubble);
    });
    container.scrollTop = container.scrollHeight;
  }

  function playElevenLabsAudio(dataUri) {
    const src = String(dataUri || "").trim();
    if (!src) return Promise.reject(new Error("No ElevenLabs audio supplied."));

    if (runtime.audioElement) {
      try {
        runtime.audioElement.pause();
        runtime.audioElement.currentTime = 0;
      } catch (_) {}
    }

    const audio = new Audio(src);
    audio.preload = "auto";
    runtime.audioElement = audio;
    audio.onplay = () => {
      runtime.speaking = true;
      runtime.voicePlaying = true;
      q("#ai-tile").classList.remove("is-thinking");
      q("#ai-tile").classList.add("is-speaking");
      q("#ai-state").textContent = "Speaking";
      setStatus(`Luna is speaking naturally in ${runtime.targetLanguage}.`, "speaking");
    };
    audio.onended = () => {
      runtime.voicePlaying = false;
      finishAssistantSpeech();
    };
    audio.onerror = () => {
      runtime.voicePlaying = false;
      finishAssistantSpeech();
    };
    return audio.play();
  }

  function speakAssistantWithFallback(text, force = false, audioDataUri = "") {
    const reply = String(text || "").trim();
    if (!reply) {
      finishAssistantSpeech();
      return;
    }

    if (!force && !runtime.callActive) return;
    stopRecognition(true);
    runtime.speaking = true;
    runtime.awaitingReply = false;
    q("#ai-tile").classList.remove("is-thinking");
    q("#ai-tile").classList.add("is-speaking");

    if (audioDataUri) {
      playElevenLabsAudio(audioDataUri)
        .then(() => {})
        .catch(() => {
          speakAssistantBrowser(reply);
        });
      return;
    }
    speakAssistantBrowser(reply);
  }

  function speakAssistantBrowser(text) {
    const reply = String(text || "").trim();
    if (!reply || !window.speechSynthesis) {
      finishAssistantSpeech();
      return;
    }
    q("#ai-state").textContent = "Speaking";
    setStatus(`Luna is replying in ${runtime.targetLanguage}.`, "speaking");
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(reply);
    utterance.lang = runtime.locale || "en-US";
    utterance.rate = 0.92;
    utterance.pitch = 1.03;
    utterance.volume = 1;
    const voice = chooseVoice(runtime.locale);
    if (voice) utterance.voice = voice;
    utterance.onend = finishAssistantSpeech;
    utterance.onerror = finishAssistantSpeech;
    runtime.currentUtterance = utterance;
    window.speechSynthesis.speak(utterance);
  }

  function chooseVoice(locale) {
    if (!window.speechSynthesis) return null;
    const voices = window.speechSynthesis.getVoices();
    const wanted = String(locale || "en-US").toLowerCase();
    const base = wanted.split("-")[0];
    return voices.find((voice) => voice.lang.toLowerCase() === wanted)
      || voices.find((voice) => voice.lang.toLowerCase().startsWith(base))
      || null;
  }

  function finishAssistantSpeech() {
    runtime.speaking = false;
    runtime.awaitingReply = false;
    q("#ai-tile").classList.remove("is-speaking");
    q("#ai-state").textContent = runtime.callActive ? "Listening" : "Ready";
    setStatus(
      runtime.callActive ? `Listening for your next sentence in ${runtime.targetLanguage}.` : "Luna's reply is ready.",
      runtime.callActive ? "live" : "idle"
    );
    if (runtime.callActive && !runtime.transcriptPaused && runtime.recognitionSupported) {
      setTimeout(() => startRecognition(), 350);
    }
  }

  function speakAssistant(text, force = false, audioDataUri = "") {
    speakAssistantWithFallback(text, force, audioDataUri);
  }

  function createRecognition() {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    runtime.recognitionSupported = Boolean(Recognition);
    const badge = q("#recognition-badge");
    const note = q("#compatibility-note");

    if (!Recognition) {
      badge.textContent = "Live transcript unavailable";
      badge.className = "recognition-badge unsupported";
      note.classList.add("error");
      note.textContent = "This browser does not expose continuous SpeechRecognition. Live video remains available; Chrome or Edge is recommended for automatic transcript processing.";
      updateControls();
      return null;
    }

    badge.textContent = "Live speech supported";
    badge.className = "recognition-badge supported";
    note.classList.remove("error");
    note.textContent = "Continuous interim transcription is available. Chrome or Edge generally provides the most reliable experience.";

    const recognition = new Recognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;
    recognition.lang = runtime.locale || "en-US";

    recognition.onstart = () => {
      runtime.recognitionActive = true;
      runtime.suppressRecognitionRestart = false;
      q("#interim-box").classList.add("is-listening");
      q("#recognition-badge").textContent = `Listening · ${runtime.locale}`;
      q("#recognition-badge").className = "recognition-badge supported";
      if (!runtime.awaitingReply && !runtime.speaking) {
        q("#ai-state").textContent = "Listening";
        setStatus(`Listening in ${runtime.targetLanguage}. Speak one sentence naturally.`, "live");
      }
    };

    recognition.onresult = (event) => {
      let interim = "";
      let finalized = "";
      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        const result = event.results[index];
        const text = result?.[0]?.transcript || "";
        if (result.isFinal) finalized += `${text} `;
        else interim += `${text} `;
      }

      const interimText = interim.trim();
      q("#interim-text").textContent = interimText || "Listening…";
      const finalText = finalized.trim();
      if (finalText) {
        q("#interim-text").textContent = finalText;
        submitUtterance(finalText, "speech");
      }
    };

    recognition.onerror = (event) => {
      runtime.recognitionActive = false;
      const error = event?.error || "speech-recognition-error";
      if (error === "aborted" || error === "no-speech") {
        if (error === "no-speech" && runtime.callActive && !runtime.awaitingReply) {
          setStatus("No speech detected yet. Keep speaking when you are ready.", "live");
        }
        return;
      }
      setStatus(`Speech recognition error: ${error}. Please continue speaking after the recognition restarts.`, "error");
      q("#recognition-badge").textContent = "Transcript needs attention";
      q("#recognition-badge").className = "recognition-badge unsupported";
    };

    recognition.onend = () => {
      runtime.recognitionActive = false;
      q("#interim-box").classList.remove("is-listening");
      if (runtime.suppressRecognitionRestart) {
        runtime.suppressRecognitionRestart = false;
        return;
      }
      if (runtime.callActive && !runtime.awaitingReply && !runtime.speaking && !runtime.transcriptPaused) {
        setTimeout(() => startRecognition(), 350);
      }
    };

    return recognition;
  }

  function startRecognition() {
    if (!runtime.callActive || runtime.transcriptPaused || runtime.awaitingReply || runtime.speaking) return;
    if (!runtime.recognitionSupported) return;
    if (!runtime.recognition) runtime.recognition = createRecognition();
    if (!runtime.recognition || runtime.recognitionActive) return;
    runtime.recognition.lang = runtime.locale || "en-US";
    runtime.suppressRecognitionRestart = false;
    try {
      runtime.recognition.start();
    } catch (error) {
      // Chrome throws when start is called while transitioning. Retry once.
      setTimeout(() => {
        if (runtime.callActive && !runtime.recognitionActive && !runtime.awaitingReply && !runtime.speaking) {
          try { runtime.recognition.start(); } catch (_) { /* recognition can be retried */ }
        }
      }, 500);
    }
  }

  function submitUtterance(text, source) {
    const transcript = String(text || "").trim();
    if (!transcript || runtime.awaitingReply) return;

    runtime.awaitingReply = true;
    runtime.lastSubmittedText = transcript;
    q("#interim-text").textContent = "Sentence sent. Luna is thinking…";
    q("#ai-tile").classList.remove("is-speaking");
    q("#ai-tile").classList.add("is-thinking");
    q("#ai-state").textContent = "Thinking";
    stopRecognition(true);
    setStatus("Luna is processing your sentence and preparing a reply.", "thinking");

    const eventId = `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
    runtime.setTriggerValue("utterance", {
      id: eventId,
      text: transcript,
      source: source || "manual",
      target_language: runtime.targetLanguage,
      locale: runtime.locale,
      created_at: new Date().toISOString(),
    });
  }

  async function startCall() {
    if (runtime.callActive) {
      endCall();
      return;
    }
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setStatus("This browser cannot access camera or microphone. Open the HTTPS Streamlit app in a modern browser.", "error");
      return;
    }

    setStatus("Requesting camera and microphone permission…", "thinking");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "user",
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      runtime.stream = stream;
      runtime.callActive = true;
      runtime.callStartedAt = Date.now();
      runtime.micMuted = false;
      runtime.cameraOff = false;
      runtime.transcriptPaused = false;
      runtime.cleaned = false;

      const video = q("#local-video");
      video.srcObject = stream;
      video.classList.add("is-live");
      q("#camera-placeholder").classList.add("hidden");
      q("#media-state").textContent = "Live";
      q("#mic-level-label").textContent = "Mic live";
      try { await video.play(); } catch (_) { /* autoplay attribute handles most browsers */ }

      if (!runtime.timerInterval) runtime.timerInterval = setInterval(updateTimer, 500);
      if (!runtime.recognition) runtime.recognition = createRecognition();
      updateControls();
      const openingReply = String(runtime.data?.assistant_reply || "").trim();
      if (openingReply) {
        setStatus(`Camera is live. Luna is greeting you in ${runtime.targetLanguage}.`, "speaking");
        setTimeout(() => speakAssistant(openingReply, true, runtime.data?.assistant_audio_data_uri || ""), 120);
      } else {
        setStatus(`Camera is live. Listening for ${runtime.targetLanguage}.`, "live");
        startRecognition();
      }
    } catch (error) {
      const message = error?.name === "NotAllowedError"
        ? "Camera or microphone permission was denied. Allow both permissions in the browser address bar and try again."
        : `Unable to start live media: ${error?.message || error}`;
      setStatus(message, "error");
      endCall(false);
    }
  }

  function endCall(showMessage = true) {
    runtime.callActive = false;
    runtime.awaitingReply = false;
    runtime.speaking = false;
    runtime.callStartedAt = null;
    stopRecognition(true);
    stopTracks();
    if (window.speechSynthesis) window.speechSynthesis.cancel();

    const video = q("#local-video");
    video.srcObject = null;
    video.classList.remove("is-live");
    q("#camera-placeholder").classList.remove("hidden");
    q("#media-state").textContent = "Camera off";
    q("#mic-level-label").textContent = "Mic ready";
    q("#call-timer").textContent = "00:00";
    q("#ai-tile").classList.remove("is-speaking", "is-thinking");
    q("#ai-state").textContent = "Ready";
    q("#interim-box").classList.remove("is-listening");
    q("#interim-text").textContent = "Your words will appear here while you speak.";
    updateControls();
    if (showMessage) setStatus("Call ended. Your transcript and learning progress remain in this session.", "idle");
  }

  function toggleMic() {
    if (!runtime.stream) return;
    runtime.micMuted = !runtime.micMuted;
    runtime.stream.getAudioTracks().forEach((track) => { track.enabled = !runtime.micMuted; });
    q("#mic-level-label").textContent = runtime.micMuted ? "Mic muted" : "Mic live";
    if (runtime.micMuted) stopRecognition(true);
    else startRecognition();
    updateControls();
  }

  function toggleCamera() {
    if (!runtime.stream) return;
    runtime.cameraOff = !runtime.cameraOff;
    runtime.stream.getVideoTracks().forEach((track) => { track.enabled = !runtime.cameraOff; });
    q("#media-state").textContent = runtime.cameraOff ? "Camera paused" : "Live";
    updateControls();
  }

  function toggleTranscript() {
    runtime.transcriptPaused = !runtime.transcriptPaused;
    if (runtime.transcriptPaused) {
      stopRecognition(true);
      setStatus("Live transcript paused. Video and microphone remain connected.", "idle");
    } else {
      setStatus(`Live transcript resumed in ${runtime.targetLanguage}.`, "live");
      startRecognition();
    }
    updateControls();
  }

  function bindControls() {
    q("#start-call").onclick = startCall;
    q("#toggle-mic").onclick = toggleMic;
    q("#toggle-camera").onclick = toggleCamera;
    q("#toggle-transcript").onclick = toggleTranscript;
    q("#replay-ai").onclick = () => speakAssistant(runtime.data?.assistant_reply || "", true, runtime.data?.assistant_audio_data_uri || "");
  }

  function restoreRuntimeUi() {
    const video = q("#local-video");
    if (runtime.callActive && runtime.stream) {
      if (video.srcObject !== runtime.stream) video.srcObject = runtime.stream;
      video.classList.add("is-live");
      q("#camera-placeholder").classList.add("hidden");
      q("#media-state").textContent = runtime.cameraOff ? "Camera paused" : "Live";
      q("#mic-level-label").textContent = runtime.micMuted ? "Mic muted" : "Mic live";
      video.play().catch(() => {});
    } else {
      video.srcObject = null;
      video.classList.remove("is-live");
      q("#camera-placeholder").classList.remove("hidden");
      q("#media-state").textContent = "Camera off";
      q("#mic-level-label").textContent = "Mic ready";
    }

    q("#ai-tile").classList.toggle("is-thinking", runtime.awaitingReply && !runtime.speaking);
    q("#ai-tile").classList.toggle("is-speaking", runtime.speaking);
    q("#ai-state").textContent = runtime.speaking
      ? "Speaking"
      : (runtime.awaitingReply ? "Thinking" : (runtime.callActive ? "Listening" : "Ready"));
    updateControls();
    updateTimer();
  }

  if (!runtime) {
    runtime = {
      setTriggerValue,
      data: safeData,
      stream: null,
      recognition: null,
      recognitionSupported: false,
      recognitionActive: false,
      suppressRecognitionRestart: false,
      callActive: false,
      callStartedAt: null,
      timerInterval: null,
      detachmentInterval: null,
      micMuted: false,
      cameraOff: false,
      transcriptPaused: false,
      awaitingReply: false,
      speaking: false,
      voicePlaying: false,
      audioElement: null,
      cleaned: false,
      locale: safeData.locale || "en-US",
      targetLanguage: safeData.target_language || "English",
      targetCharacter: safeData.character_name || "Luna",
      difficulty: safeData.difficulty || "Beginner",
      lastReplyId: Number(safeData.assistant_reply_id || 0),
      lastResetToken: Number(safeData.reset_token || 0),
      lastSubmittedText: "",
    };
    parentElement.__lingglotRealtimeRuntime = runtime;

    bindControls();

    runtime.recognition = createRecognition();
    updateControls();
    runtime.detachmentInterval = setInterval(() => {
      if (!parentElement.isConnected) cleanupRuntime();
    }, 1000);
  }

  runtime.setTriggerValue = setTriggerValue;
  runtime.data = safeData;
  bindControls();

  const previousLocale = runtime.locale;
  runtime.locale = safeData.locale || "en-US";
  runtime.targetLanguage = safeData.target_language || "English";
  runtime.targetCharacter = safeData.character_name || "Luna";
  runtime.difficulty = safeData.difficulty || "Beginner";

  q("#lesson-label").textContent = `${runtime.targetLanguage} · ${runtime.difficulty}`;
  q("#character-call-name").textContent = `${runtime.targetCharacter || "AI partner"} video call`;
  q("#ai-participant-name").textContent = `${runtime.targetCharacter || "AI partner"} · AI tutor`;
  q("#voice-provider").textContent = String(safeData.voice_provider || "Browser voice");
  q("#latest-ai-reply").textContent = String(safeData.assistant_reply || "Start the call and say a sentence.");
  if (safeData.avatar_data_uri) q("#luna-avatar").src = safeData.avatar_data_uri;
  renderHistory(safeData.history || []);
  restoreRuntimeUi();

  const resetToken = Number(safeData.reset_token || 0);
  if (resetToken !== runtime.lastResetToken) {
    runtime.lastResetToken = resetToken;
    runtime.awaitingReply = false;
    q("#interim-text").textContent = "Transcript cleared. Continue speaking when ready.";
  }

  if (runtime.recognition && previousLocale !== runtime.locale) {
    runtime.recognition.lang = runtime.locale;
    if (runtime.callActive && !runtime.awaitingReply && !runtime.speaking && !runtime.transcriptPaused) {
      stopRecognition(true);
      setTimeout(() => startRecognition(), 350);
    }
  }

  const replyId = Number(safeData.assistant_reply_id || 0);
  if (replyId > 0 && replyId !== runtime.lastReplyId) {
    runtime.lastReplyId = replyId;
    runtime.awaitingReply = false;
    q("#ai-tile").classList.remove("is-thinking");
    const reply = String(safeData.assistant_reply || "").trim();
    if (reply) speakAssistant(reply, false, safeData.assistant_audio_data_uri || "");
    else finishAssistantSpeech();
  }
}
"""


_REALTIME_CALL_COMPONENT = st.components.v2.component(
    "lingglot_realtime_video_call",
    html=REALTIME_CALL_HTML,
    css=REALTIME_CALL_CSS,
    js=REALTIME_CALL_JS,
    isolate_styles=True,
)


def svg_data_uri(path: str | Path) -> str:
    """Return an SVG file as a browser-safe data URI."""

    svg_bytes = Path(path).read_bytes()
    encoded = base64.b64encode(svg_bytes).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def serialize_call_history(
    messages: Sequence[Mapping[str, Any]],
    *,
    limit: int = 30,
) -> list[dict[str, Any]]:
    """Keep only JSON-safe fields needed by the live transcript UI."""

    serialized: list[dict[str, Any]] = []
    for message in list(messages)[-limit:]:
        serialized.append(
            {
                "role": "user" if message.get("role") == "user" else "assistant",
                "content": str(message.get("content", "")),
                "feedback": str(message.get("feedback", "")) if message.get("feedback") else "",
                "points": int(message.get("points", 0) or 0),
            }
        )
    return serialized


def mount_realtime_call(
    *,
    target_language: str,
    locale: str,
    difficulty: str,
    character_name: str = "Luna",
    assistant_reply: str,
    assistant_reply_id: int,
    assistant_audio_data_uri: str = "",
    voice_provider: str = "Browser voice",
    history: Sequence[Mapping[str, Any]],
    avatar_path: str | Path,
    reset_token: int,
    key: str,
    on_utterance: Callable[[], None],
    height: int = 1060,
):
    """Mount the call component and return its Streamlit component result."""

    return _REALTIME_CALL_COMPONENT(
        data={
            "target_language": target_language,
            "locale": locale,
            "difficulty": difficulty,
            "character_name": character_name,
            "assistant_reply": assistant_reply,
            "assistant_reply_id": int(assistant_reply_id),
            "assistant_audio_data_uri": assistant_audio_data_uri,
            "voice_provider": voice_provider,
            "history": serialize_call_history(history),
            "avatar_data_uri": svg_data_uri(avatar_path),
            "reset_token": int(reset_token),
        },
        key=key,
        on_utterance_change=on_utterance,
        width="stretch",
        height=height,
    )
