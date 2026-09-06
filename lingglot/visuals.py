"""Static HTML and SVG helpers for the Lingglot visual layer."""

from __future__ import annotations

from html import escape
from typing import Iterable, Mapping

PALETTES = [
    ("#F7B7A3", "#F49E89"),
    ("#F2BFD6", "#E89BBE"),
    ("#FCD6B6", "#F4B98E"),
    ("#E7B6D9", "#D193C2"),
    ("#F8C2B0", "#EE9F89"),
    ("#F4C9DC", "#E0A2C3"),
]

CHARACTERS = [
    ("Luna", "Calm and patient"),
    ("Milo", "Wise and witty"),
    ("Pico", "Curious and cheerful"),
    ("Nori", "Energetic and warm"),
    ("Sol", "Thoughtful and kind"),
    ("Bibi", "Kind and cute"),
]


def character_svg(
    index: int,
    size: int = 140,
    id_prefix: str = "character",
    include_background: bool = False,
) -> str:
    """Return a friendly procedural character inspired by the Lovable source."""

    c1, c2 = PALETTES[index % len(PALETTES)]
    gradient_id = f"{id_prefix}-gradient-{index}"
    if index % 2 == 0:
        ears = (
            f'<circle cx="28" cy="22" r="11" fill="{c2}"/>'
            f'<circle cx="72" cy="22" r="11" fill="{c2}"/>'
        )
    else:
        ears = (
            f'<ellipse cx="22" cy="30" rx="9" ry="13" fill="{c2}"/>'
            f'<ellipse cx="78" cy="30" rx="9" ry="13" fill="{c2}"/>'
        )

    background = ""
    if include_background:
        background = (
            '<rect width="100" height="100" rx="24" fill="#FFF2E5"/>'
            '<circle cx="18" cy="18" r="15" fill="#FFCBB6" opacity=".45"/>'
            '<circle cx="84" cy="82" r="22" fill="#FFC3E5" opacity=".35"/>'
        )

    return f"""
<svg class="lingglot-character-svg" width="{size}" height="{size}"
     viewBox="0 0 100 100" role="img" aria-label="Friendly Lingglot character"
     xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="{gradient_id}" cx="50%" cy="40%" r="70%">
      <stop offset="0%" stop-color="{c1}"/>
      <stop offset="100%" stop-color="{c2}"/>
    </radialGradient>
  </defs>
  {background}
  {ears}
  <circle cx="50" cy="55" r="32" fill="url(#{gradient_id})"/>
  <ellipse cx="50" cy="63" rx="17" ry="12" fill="#FFF6EE" opacity=".34"/>
  <circle cx="35" cy="62" r="4" fill="#F49AB0" opacity=".55"/>
  <circle cx="65" cy="62" r="4" fill="#F49AB0" opacity=".55"/>
  <circle cx="40" cy="52" r="3.2" fill="#2B1D24"/>
  <circle cx="60" cy="52" r="3.2" fill="#2B1D24"/>
  <circle cx="41" cy="51" r="1" fill="#FFFFFF"/>
  <circle cx="61" cy="51" r="1" fill="#FFFFFF"/>
  <path d="M44 66 Q50 71 56 66" stroke="#2B1D24" stroke-width="2"
        stroke-linecap="round" fill="none"/>
</svg>
""".strip()


def logo_icon_svg(size: int = 64) -> str:
    return f"""
<svg width="{size}" height="{size}" viewBox="0 0 64 64"
     xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Lingglot logo">
  <defs>
    <linearGradient id="lingglot-logo-gradient" x1="6" y1="8" x2="58" y2="58"
                    gradientUnits="userSpaceOnUse">
      <stop stop-color="#FF6A3D"/>
      <stop offset=".56" stop-color="#FF4F9A"/>
      <stop offset="1" stop-color="#FF4DC4"/>
    </linearGradient>
  </defs>
  <path d="M12 10h40a8 8 0 0 1 8 8v25a8 8 0 0 1-8 8H31L18 60v-9h-6a8 8 0 0 1-8-8V18a8 8 0 0 1 8-8Z"
        fill="url(#lingglot-logo-gradient)"/>
  <circle cx="24" cy="30" r="3" fill="#FFF9ED"/>
  <circle cx="40" cy="30" r="3" fill="#FFF9ED"/>
  <path d="M24 39c4.5 4 11.5 4 16 0" stroke="#FFF9ED" stroke-width="3"
        stroke-linecap="round" fill="none"/>
</svg>
""".strip()


def hero_phone_html() -> str:
    bars = "".join(
        f'<span style="height:{28 + ((i * 17) % 68)}%;animation-delay:{(i % 8) * 0.08:.2f}s"></span>'
        for i in range(24)
    )
    luna = character_svg(1, size=160, id_prefix="hero-phone")
    return f"""
<div class="phone-wrap" aria-label="Lingglot conversation preview">
  <div class="phone-glow"></div>
  <div class="phone-shell">
    <div class="phone-screen">
      <div class="phone-status"><span>9:41</span><span>•••</span></div>
      <div class="phone-heading">
        <small>Spanish lesson</small>
        <strong>At the cafe with Luna</strong>
      </div>
      <div class="phone-video">
        <div class="phone-live"><i></i> LIVE</div>
        <div class="phone-character">{luna}</div>
        <div class="phone-self">&#128100;</div>
      </div>
      <div class="phone-transcript">
        <small>Transcript</small>
        <div class="transcript-line">Un cafe con leche, por favor.</div>
        <div class="feedback-line"><span>Great pronunciation!</span><b>A2 &#10003;</b></div>
      </div>
      <div class="phone-waveform">{bars}</div>
      <div class="phone-controls">
        <span>&#128266;</span>
        <span class="phone-mic">&#127908;<i></i></span>
        <span>&#127909;</span>
      </div>
    </div>
  </div>
</div>
""".strip()


def character_grid_html() -> str:
    cards = []
    for index, (name, trait) in enumerate(CHARACTERS):
        avatar = character_svg(
            index,
            size=132,
            id_prefix="crew",
            include_background=False,
        )
        cards.append(
            f"""
<div class="crew-card">
  <div class="crew-avatar">{avatar}</div>
  <div class="crew-meta">
    <div><strong>{escape(name)}</strong><small>{escape(trait)}</small></div>
    <span class="crew-audio">&#128266;</span>
  </div>
</div>
""".strip()
        )
    return '<div class="crew-grid">' + "".join(cards) + "</div>"


def feature_grid_html() -> str:
    features = [
        (
            "01",
            "Real conversation",
            "Practice naturally with Luna in ten target languages and receive a warm follow-up question.",
        ),
        (
            "02",
            "Playful practice",
            "Build vocabulary, role-play everyday situations, and expand sentences through focused mini-games.",
        ),
        (
            "03",
            "Adaptive progress",
            "Earn points while the difficulty bandit and learner-clustering model adapt to your session.",
        ),
    ]
    cards = []
    for number, title, description in features:
        cards.append(
            f"""
<div class="feature-card">
  <span class="feature-number">{number}</span>
  <h3>{escape(title)}</h3>
  <p>{escape(description)}</p>
</div>
""".strip()
        )
    return '<div class="feature-grid">' + "".join(cards) + "</div>"


def cta_banner_html() -> str:
    left = character_svg(0, size=112, id_prefix="cta-left")
    right = character_svg(3, size=126, id_prefix="cta-right")
    return f"""
<div class="cta-banner">
  <div class="cta-character cta-left">{left}</div>
  <div class="cta-copy">
    <span class="eyebrow eyebrow-light">Friendly practice, no pressure</span>
    <h2>Your next conversation is one tap away.</h2>
    <p>Choose a language, meet Luna, and begin with one simple sentence.</p>
  </div>
  <div class="cta-character cta-right">{right}</div>
</div>
""".strip()


def progress_tip_html(title: str, text: str) -> str:
    return f"""
<div class="ai-tip">
  <span class="ai-tip-icon">&#10022;</span>
  <div><strong>{escape(title)}</strong><p>{escape(text)}</p></div>
</div>
""".strip()


def stat_strip_html(items: Mapping[str, str | int | float]) -> str:
    cards = []
    for label, value in items.items():
        cards.append(
            f"""
<div class="stat-chip"><strong>{escape(str(value))}</strong><span>{escape(label)}</span></div>
""".strip()
        )
    return '<div class="stat-strip">' + "".join(cards) + "</div>"


def progress_stat_strip_html(
    progress_percent: int | float,
    items: Mapping[str, str | int | float],
    *,
    label: str = "Practice progress",
    helper: str = "Toward your 100-point practice goal",
) -> str:
    """Render a progress bar as the first stat card, followed by stat chips.

    The progress value is clamped to 0-100 so the generated HTML stays valid
    even if a caller passes a value outside the expected range.
    """

    progress = max(0, min(100, int(round(float(progress_percent)))))
    cards = [
        f"""
<div class="stat-chip stat-progress-chip">
  <div class="stat-progress-heading">
    <span>{escape(label)}</span>
    <strong>{progress}%</strong>
  </div>
  <div class="stat-progress-track" role="progressbar" aria-label="{escape(label)}"
       aria-valuemin="0" aria-valuemax="100" aria-valuenow="{progress}">
    <div class="stat-progress-fill" style="width:{progress}%"></div>
  </div>
  <small>{escape(helper)}</small>
</div>
""".strip()
    ]

    for item_label, value in items.items():
        cards.append(
            f"""
<div class="stat-chip"><strong>{escape(str(value))}</strong><span>{escape(item_label)}</span></div>
""".strip()
        )

    return '<div class="stat-strip">' + "".join(cards) + "</div>"


def pills_html(items: Iterable[str]) -> str:
    return '<div class="pill-row">' + "".join(
        f'<span class="soft-pill">{escape(item)}</span>' for item in items
    ) + "</div>"


def video_call_stage_html(
    *,
    target_language: str,
    difficulty: str,
    is_live: bool,
    last_reply: str = "",
) -> str:
    """Render the AI partner side of the video-call experience."""

    status_label = "LIVE" if is_live else "READY"
    status_class = "is-live" if is_live else "is-ready"
    luna = character_svg(0, size=260, id_prefix="video-call-luna", include_background=False)
    reply = escape(last_reply or "Start the camera, then say or type a sentence to begin.")
    return f"""
<div class="video-call-ai-stage {status_class}" aria-label="AI language video call with Luna">
  <div class="video-call-stage-top">
    <span class="video-call-live-badge"><i></i>{status_label}</span>
    <span class="video-call-lesson-chip">{escape(target_language)} · {escape(difficulty)}</span>
  </div>
  <div class="video-call-orbit orbit-one"></div>
  <div class="video-call-orbit orbit-two"></div>
  <div class="video-call-avatar-wrap">
    <div class="video-call-avatar-glow"></div>
    <div class="video-call-avatar">{luna}</div>
    <div class="video-call-speech-ring ring-one"></div>
    <div class="video-call-speech-ring ring-two"></div>
  </div>
  <div class="video-call-partner-name">
    <strong>Luna</strong>
    <span>Your AI language partner</span>
  </div>
  <div class="video-call-caption">
    <small>Latest reply</small>
    <p>{reply}</p>
  </div>
  <div class="video-call-wave" aria-hidden="true">
    <span></span><span></span><span></span><span></span><span></span><span></span>
    <span></span><span></span><span></span><span></span><span></span><span></span>
  </div>
</div>
""".strip()


def video_call_status_html(
    *,
    camera_live: bool,
    target_language: str,
    difficulty: str,
) -> str:
    """Render a compact call-status strip below the media stage."""

    camera = "Connected" if camera_live else "Ready to connect"
    camera_class = "ok" if camera_live else "idle"
    return f"""
<div class="video-call-status-strip">
  <span class="video-call-status-item {camera_class}"><i></i>Camera + mic: {escape(camera)}</span>
  <span class="video-call-status-item">Practice: {escape(target_language)}</span>
  <span class="video-call-status-item">Level: {escape(difficulty)}</span>
</div>
""".strip()
