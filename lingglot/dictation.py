"""Small browser speech-to-text dictation component for the Conversation composer."""

from __future__ import annotations

from typing import Any

import streamlit as st


HTML = r"""
<div class="dictation-shell">
  <button id="dictate" class="dictate-button" type="button" aria-label="Dictate">
    <span class="dictate-icon">🎙</span><span id="dictate-label">Dictate</span>
  </button>
  <span id="dictate-status" class="dictate-status">Ready</span>
</div>
"""

CSS = r"""
:host { display:block; width:100%; }
* { box-sizing:border-box; }
.dictation-shell { display:flex; align-items:center; justify-content:center; gap:8px; min-height:44px; }
.dictate-button { border:1px solid #edd6cd; border-radius:14px; padding:10px 13px; background:#fffaf5; color:#6f5049; font-weight:750; cursor:pointer; transition:.18s ease; }
.dictate-button:hover { border-color:#ff9a78; transform:translateY(-1px); }
.dictate-button.is-listening { background:linear-gradient(135deg,#ff704d,#ff4f9a); color:#fff; border-color:transparent; box-shadow:0 10px 22px rgba(255,79,154,.2); }
.dictate-status { font-size:.7rem; color:#92756e; }
"""

JS = r"""
export default function(component) {
const { setTriggerValue, parentElement } = component;
const root = parentElement.querySelector('.dictation-shell');
if (!root || !parentElement) return;
const q = (selector) => root.querySelector(selector);
let runtime = parentElement.__lingglotDictationRuntime;
if (!runtime) {
  runtime = { listening:false, recognition:null, locale:'en-US', counter:0 };
  parentElement.__lingglotDictationRuntime = runtime;
}

function update() {
  q('#dictate').classList.toggle('is-listening', runtime.listening);
  q('#dictate-label').textContent = runtime.listening ? 'Stop' : 'Dictate';
  q('#dictate-status').textContent = runtime.listening ? 'Listening…' : 'Ready';
}

function makeRecognition() {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) {
    q('#dictate-status').textContent = 'Chrome/Edge recommended';
    return null;
  }
  const r = new Recognition();
  r.continuous = false;
  r.interimResults = true;
  r.maxAlternatives = 1;
  r.lang = runtime.locale || 'en-US';
  r.onstart = () => { runtime.listening = true; update(); };
  r.onresult = (event) => {
    let finalText = '';
    let interimText = '';
    for (let i = event.resultIndex; i < event.results.length; i += 1) {
      const result = event.results[i];
      const value = String(result?.[0]?.transcript || '').trim();
      if (result.isFinal) finalText += `${value} `;
      else interimText += `${value} `;
    }
    q('#dictate-status').textContent = interimText.trim() || (finalText.trim() ? 'Captured' : 'Listening…');
    if (finalText.trim()) {
      runtime.counter += 1;
      setTriggerValue('dictation', { id: `${Date.now()}-${runtime.counter}`, text: finalText.trim() });
    }
  };
  r.onerror = (event) => {
    runtime.listening = false; update();
    q('#dictate-status').textContent = String(event?.error || 'Speech recognition error');
  };
  r.onend = () => { runtime.listening = false; update(); };
  return r;
}

q('#dictate').onclick = () => {
  if (!runtime.recognition) runtime.recognition = makeRecognition();
  if (!runtime.recognition) return;
  if (runtime.listening) {
    try { runtime.recognition.stop(); } catch (_) {}
  } else {
    try { runtime.recognition.start(); } catch (_) {}
  }
};

runtime.locale = runtime.locale || 'en-US';
update();
}
"""

_DICTATION_COMPONENT = st.components.v2.component(
    'lingglot_dictation',
    html=HTML,
    css=CSS,
    js=JS,
    isolate_styles=True,
)


def mount_dictation(*, locale: str = 'en-US', key: str = 'lingglot_dictation') -> Any:
    """Mount the compact Dictation button."""
    return _DICTATION_COMPONENT(
        data={'locale': locale},
        key=key,
        width='stretch',
        height=46,
    )
