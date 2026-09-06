"""Lingglot: Lovable-inspired Streamlit interface with the original AI logic."""

from __future__ import annotations

from html import escape
from pathlib import Path
import json
import sys
from typing import Any, Dict

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

try:
    from streamlit_webrtc import WebRtcMode, webrtc_streamer

    WEBRTC_AVAILABLE = True
except Exception:
    WebRtcMode = None
    webrtc_streamer = None
    WEBRTC_AVAILABLE = False

# Streamlit Community Cloud executes the app from the repository root. Add the
# entrypoint directory explicitly so the bundled local package is importable
# even when the launcher changes sys.path behavior.
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_REQUIRED_LOCAL_FILES = (
    ROOT / "lingglot" / "__init__.py",
    ROOT / "lingglot" / "core.py",
    ROOT / "lingglot" / "language_detection.py",
    ROOT / "lingglot" / "visuals.py",
)
_missing_local_files = [path for path in _REQUIRED_LOCAL_FILES if not path.is_file()]
if _missing_local_files:
    st.set_page_config(page_title="Lingglot deployment check", page_icon="⚠️")
    st.error(
        "The GitHub deployment is incomplete: the local `lingglot` package "
        "is missing or is not beside `streamlit_app.py`."
    )
    st.markdown("Your repository root must contain this structure:")
    st.code(
        """streamlit_app.py
requirements.txt
lingglot/
  __init__.py
  core.py
  language_detection.py
  visuals.py
assets/
.streamlit/config.toml""",
        language="text",
    )
    st.write("Missing files:")
    for missing_path in _missing_local_files:
        st.code(str(missing_path.relative_to(ROOT)), language="text")
    st.info(
        "Extract the supplied ZIP first, then upload every extracted file and "
        "folder to GitHub. GitHub and Streamlit do not unpack a ZIP stored as "
        "a repository file."
    )
    st.stop()

from lingglot.core import (
    ADVISOR,
    APP_NAME,
    AUTHOR,
    DIFFICULTY_LEVELS,
    MENTOR,
    MODEL_NAME,
    SUPPORTED_LANGUAGES,
    DifficultyBandit,
    LearnerState,
    build_profile_model,
    calculate_skill_scores,
    check_vocab_answer,
    generate_roleplay_prompt,
    generate_vocab_question,
    language_learning_turn,
    learner_history_dataframe,
    predict_learner_profile,
    sentence_expansion_challenge,
)
from lingglot.visuals import (
    character_grid_html,
    character_svg,
    cta_banner_html,
    feature_grid_html,
    hero_phone_html,
    pills_html,
    progress_tip_html,
    progress_stat_strip_html,
    video_call_stage_html,
    video_call_status_html,
)

ASSET_DIR = ROOT / "assets"
CSS_PATH = ASSET_DIR / "styles.css"
LOGO_HORIZONTAL = ASSET_DIR / "logo-horizontal.svg"
LOGO_ICON = ASSET_DIR / "logo-icon.svg"
LUNA_IMAGE = ASSET_DIR / "characters" / "luna.svg"

st.set_page_config(
    page_title=APP_NAME,
    page_icon=str(LOGO_ICON),
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "About": (
            "Lingglot is an AI language-learning prototype created by "
            f"{AUTHOR}, mentored by {MENTOR}."
        )
    },
)

st.html(CSS_PATH)
st.logo(str(LOGO_HORIZONTAL), icon_image=str(LOGO_ICON))




LANGUAGE_VOICE_LOCALES = {
    "English": "en-US",
    "Spanish": "es-ES",
    "French": "fr-FR",
    "German": "de-DE",
    "Italian": "it-IT",
    "Portuguese": "pt-BR",
    "Chinese": "zh-CN",
    "Japanese": "ja-JP",
    "Korean": "ko-KR",
    "Arabic": "ar-SA",
}


def build_rtc_configuration() -> Dict[str, Any]:
    """Return STUN config plus optional TURN credentials from Streamlit secrets."""

    ice_servers: list[Dict[str, Any]] = [
        {"urls": ["stun:stun.l.google.com:19302"]}
    ]
    try:
        turn_url = st.secrets.get("TURN_URL")
        turn_username = st.secrets.get("TURN_USERNAME")
        turn_credential = st.secrets.get("TURN_CREDENTIAL")
    except Exception:
        turn_url = turn_username = turn_credential = None

    if turn_url and turn_username and turn_credential:
        ice_servers.append(
            {
                "urls": [str(turn_url)],
                "username": str(turn_username),
                "credential": str(turn_credential),
            }
        )
    return {"iceServers": ice_servers}


def render_browser_tts(text: str, language: str) -> None:
    """Provide a browser-native text-to-speech control for Luna's reply."""

    if not text:
        return
    payload = json.dumps(str(text))
    locale = json.dumps(LANGUAGE_VOICE_LOCALES.get(language, "en-US"))
    components.html(
        f"""
<!doctype html>
<html>
<head>
<style>
  body {{ margin: 0; font-family: system-ui, sans-serif; background: transparent; }}
  .tts-row {{ display: flex; gap: 8px; align-items: center; }}
  button {{
    border: 1px solid #eddad0; border-radius: 999px; padding: 9px 14px;
    background: rgba(255,255,255,.92); color: #351c1c; font-weight: 700;
    cursor: pointer; box-shadow: 0 5px 18px -12px rgba(83,32,25,.45);
  }}
  button:hover {{ border-color: #ff9173; background: #fff8f1; }}
  .stop {{ padding-inline: 11px; }}
  span {{ color: #795b56; font-size: 12px; }}
</style>
</head>
<body>
<div class="tts-row">
  <button id="speak">🔊 Hear Luna</button>
  <button id="stop" class="stop" aria-label="Stop speech">■</button>
  <span>Uses your browser's installed voice.</span>
</div>
<script>
const text = {payload};
const locale = {locale};
const speak = () => {{
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = locale;
  utterance.rate = 0.92;
  utterance.pitch = 1.04;
  window.speechSynthesis.speak(utterance);
}};
document.getElementById('speak').addEventListener('click', speak);
document.getElementById('stop').addEventListener('click', () => window.speechSynthesis.cancel());
</script>
</body>
</html>
""",
        height=56,
        scrolling=False,
    )


def submit_video_call_turn(
    transcript: str,
    target_language: str,
    difficulty: str,
    *,
    auto_adapt: bool,
    use_llm: bool,
) -> None:
    """Run one video-call transcript through the same learning engine."""

    prompt = transcript.strip()
    if not prompt:
        return
    st.session_state.video_messages.append({"role": "user", "content": prompt})
    result, updated_state, updated_bandit = language_learning_turn(
        st.session_state.learner_state,
        st.session_state.bandit,
        prompt,
        target_language,
        difficulty,
        auto_adapt_difficulty=auto_adapt,
        use_llm=use_llm,
    )
    st.session_state.learner_state = updated_state
    st.session_state.bandit = updated_bandit
    st.session_state.video_last_reply = result["ai_reply"]
    st.session_state.video_messages.append(
        {
            "role": "assistant",
            "content": result["ai_reply"],
            "feedback": result["feedback"],
            "points": result["points"],
            "total_points": result["total_points"],
            "difficulty": result["difficulty"],
            "profile": result["profile"],
            "bandit": result["bandit"],
            "llm_error": result.get("llm_error"),
        }
    )

def default_messages() -> list[Dict[str, Any]]:
    return [
        {
            "role": "assistant",
            "content": (
                "Hello! I am Luna, your friendly language partner. Choose a "
                "target language, then tell me something about your day."
            ),
        }
    ]


def initialize_session_state() -> None:
    defaults: Dict[str, Any] = {
        "learner_state": LearnerState(),
        "bandit": DifficultyBandit(),
        "messages": default_messages(),
        "current_vocab_answer": None,
        "current_vocab_question": (
            "Generate a vocabulary question when you are ready."
        ),
        "vocab_scored": False,
        "roleplay_prompt": (
            "Generate a role-play scenario to practice an everyday situation."
        ),
        "sentence_prompt": (
            "Generate a sentence expansion challenge to stretch your fluency."
        ),
        "pending_challenge": None,
        "video_messages": [
            {
                "role": "assistant",
                "content": (
                    "Hi! I am Luna. Start your camera and microphone, then "
                    "practice with me in your target language."
                ),
            }
        ],
        "video_last_reply": (
            "Start the camera, then say or type a sentence to begin."
        ),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_all_state() -> None:
    keys_to_clear = [
        "learner_state",
        "bandit",
        "messages",
        "current_vocab_answer",
        "current_vocab_question",
        "vocab_scored",
        "roleplay_prompt",
        "sentence_prompt",
        "pending_challenge",
        "learner_name_widget",
        "target_language_widget",
        "manual_difficulty_widget",
        "auto_adapt_widget",
        "use_llm_widget",
        "games_language_widget",
        "games_difficulty_widget",
        "vocab_answer_input",
        "roleplay_draft",
        "sentence_draft",
        "video_messages",
        "video_last_reply",
        "video_target_language_widget",
        "video_difficulty_widget",
        "video_auto_adapt_widget",
        "video_use_llm_widget",
        "video_transcript_input",
        "video_voice_note",
    ]
    for key in keys_to_clear:
        st.session_state.pop(key, None)
    initialize_session_state()


def clear_conversation() -> None:
    st.session_state.messages = default_messages()


def render_page_intro(kicker: str, title: str, subtitle: str) -> None:
    st.html(
        f"""
<div class="page-kicker">{escape(kicker)}</div>
<h1 class="page-title">{escape(title)}</h1>
<p class="page-subtitle">{escape(subtitle)}</p>
"""
    )


def render_home() -> None:
    with st.container(key="home-hero"):
        copy_col, phone_col = st.columns(
            [1.12, 0.88],
            gap="large",
            vertical_alignment="center",
        )
        with copy_col:
            st.html(
                """
<div class="hero-copy">
  <span class="eyebrow">AI-powered oral fluency</span>
  <h1>Talk your way to <span class="text-gradient-warm">fluency.</span></h1>
  <p>Lingglot pairs you with a friendly AI character for natural language practice. Get instant feedback, earn points, play mini-games, and watch your learning profile evolve.</p>
</div>
"""
            )

            action_one, action_two, action_three = st.columns(3, gap="small")
            with action_one:
                if st.button(
                    "Start speaking",
                    type="primary",
                    icon=":material/arrow_forward:",
                    width="stretch",
                    key="home-start-speaking",
                ):
                    st.switch_page(PRACTICE_PAGE)
            with action_two:
                if st.button(
                    "Video call",
                    icon=":material/video_call:",
                    width="stretch",
                    key="home-video-call",
                ):
                    st.switch_page(VIDEO_CALL_PAGE)
            with action_three:
                if st.button(
                    "Mini-games",
                    icon=":material/sports_esports:",
                    width="stretch",
                    key="home-explore-games",
                ):
                    st.switch_page(GAMES_PAGE)

            mini_avatars = "".join(
                f'<span>{character_svg(i, size=34, id_prefix="hero-mini")}</span>'
                for i in range(4)
            )
            st.html(
                f"""
<div class="hero-mini-crew">
  <div class="hero-mini-avatars">{mini_avatars}</div>
  <span>A variety of warm practice partners, starting with Luna.</span>
</div>
"""
            )

        with phone_col:
            st.html(hero_phone_html())

    st.html(
        """
<div class="section-heading">
  <span class="eyebrow">Meet the crew</span>
  <h2>Six friends. <span class="text-gradient-warm">Six personalities.</span></h2>
  <p>The character system from the Lovable design is recreated as lightweight SVG artwork, so the repository stays fast and self-contained.</p>
</div>
"""
    )
    st.html(character_grid_html())

    st.html(
        """
<div class="section-heading">
  <span class="eyebrow">Everything in one place</span>
  <h2>Practice that feels <span class="text-gradient-warm">alive.</span></h2>
  <p>The polished visual system is connected directly to the original conversation engine, rewards, mini-games, adaptive difficulty, and learner analytics.</p>
</div>
"""
    )
    st.html(feature_grid_html())

    st.html(cta_banner_html())
    left_space, cta_col, right_space = st.columns([1.2, 1, 1.2])
    del left_space, right_space
    with cta_col:
        if st.button(
            "Begin a conversation",
            type="primary",
            icon=":material/mic:",
            width="stretch",
            key="home-bottom-cta",
        ):
            st.switch_page(PRACTICE_PAGE)


def render_feedback_card(message: Dict[str, Any]) -> None:
    feedback = escape(str(message.get("feedback", ""))).replace("\n", "<br>")
    points = escape(str(message.get("points", 0)))
    difficulty = escape(str(message.get("difficulty", "")))
    profile = escape(str(message.get("profile", "")))
    total_points = escape(str(message.get("total_points", "")))
    st.html(
        f"""
<div class="tutor-feedback-card">
  <strong>Tutor feedback</strong>
  <p>{feedback}</p>
  <div class="feedback-meta">
    <span>+{points} points</span>
    <span>{total_points} total</span>
    <span>{difficulty}</span>
    <span>{profile}</span>
  </div>
</div>
"""
    )


def render_practice() -> None:
    render_page_intro(
        "AI conversation",
        "Practice with Luna",
        (
            "Choose a language and difficulty, then write naturally. Luna will "
            "reply, offer brief tutor feedback, award points, and update the "
            "adaptive learner profile."
        ),
    )

    state: LearnerState = st.session_state.learner_state
    settings_col, chat_col = st.columns(
        [0.34, 0.66],
        gap="large",
        vertical_alignment="top",
    )

    with settings_col:
        with st.container(key="practice-settings"):
            st.image(str(LUNA_IMAGE), width="stretch")
            st.markdown("### Luna")
            st.caption("Calm, patient, and always ready for one more sentence.")

            learner_name = st.text_input(
                "Learner name",
                value=state.username,
                key="learner_name_widget",
            )
            target_language = st.selectbox(
                "Target language",
                SUPPORTED_LANGUAGES,
                index=(
                    SUPPORTED_LANGUAGES.index(state.target_language)
                    if state.target_language in SUPPORTED_LANGUAGES
                    else 1
                ),
                key="target_language_widget",
            )
            manual_difficulty = st.segmented_control(
                "Manual difficulty",
                DIFFICULTY_LEVELS,
                default=(
                    state.difficulty
                    if state.difficulty in DIFFICULTY_LEVELS
                    else "Beginner"
                ),
                key="manual_difficulty_widget",
                width="stretch",
            )
            auto_adapt = st.toggle(
                "Use adaptive difficulty",
                value=True,
                key="auto_adapt_widget",
                help=(
                    "The epsilon-greedy bandit chooses a level and learns from "
                    "the rewards earned in this session."
                ),
            )
            use_llm = st.toggle(
                "Use local Hugging Face model",
                value=False,
                key="use_llm_widget",
                help=(
                    "Requires requirements-full.txt and downloads "
                    f"{MODEL_NAME}. The fallback engine works without it."
                ),
            )

            state.username = learner_name
            state.target_language = target_language

            st.html(
                pills_html(
                    [
                        target_language,
                        "Adaptive" if auto_adapt else str(manual_difficulty),
                        "Local LLM" if use_llm else "Fast fallback",
                    ]
                )
            )

            clear_col, reset_col = st.columns(2, gap="small")
            with clear_col:
                st.button(
                    "New chat",
                    icon=":material/refresh:",
                    width="stretch",
                    key="clear-conversation-button",
                    on_click=clear_conversation,
                )
            with reset_col:
                st.button(
                    "Reset all",
                    icon=":material/restart_alt:",
                    width="stretch",
                    key="reset-all-button",
                    on_click=reset_all_state,
                )

            st.caption(
                "Default mode is lightweight and does not require an external "
                "API key. Optional model mode can require substantial memory."
            )

    with chat_col:
        with st.container(key="practice-chat"):
            profile = predict_learner_profile(state)
            practice_progress = min(100, max(0, state.total_points))
            st.html(
                progress_stat_strip_html(
                    practice_progress,
                    {
                        "Conversation turns": state.conversation_turns,
                        "Current level": state.difficulty,
                        "Learner profile": profile,
                    },
                    label="Practice progress",
                    helper="Toward your 100-point practice goal",
                )
            )

            pending = st.session_state.get("pending_challenge")
            if pending:
                st.info(
                    f"Mini-game prompt brought into practice: {pending}",
                    icon=":material/lightbulb:",
                )
                if st.button(
                    "Dismiss prompt",
                    key="dismiss-pending-challenge",
                    icon=":material/close:",
                ):
                    st.session_state.pending_challenge = None
                    st.rerun()

            with st.container(
                height=520,
                key="chat-scroll",
                border=False,
                autoscroll=True,
            ):
                for message in st.session_state.messages:
                    avatar = str(LUNA_IMAGE) if message["role"] == "assistant" else None
                    with st.chat_message(message["role"], avatar=avatar):
                        st.markdown(str(message.get("content", "")))
                        if message.get("feedback"):
                            render_feedback_card(message)
                        if message.get("llm_error"):
                            st.caption(
                                "The local model could not load, so Luna used "
                                "the built-in fallback response."
                            )

            prompt = st.chat_input(
                f"Write something in {target_language}...",
                key="practice-chat-input",
                max_chars=1200,
            )
            if prompt:
                st.session_state.messages.append(
                    {"role": "user", "content": prompt}
                )
                with st.spinner("Luna is thinking..."):
                    result, updated_state, updated_bandit = language_learning_turn(
                        st.session_state.learner_state,
                        st.session_state.bandit,
                        prompt,
                        target_language,
                        str(manual_difficulty or "Beginner"),
                        auto_adapt_difficulty=auto_adapt,
                        use_llm=use_llm,
                    )
                st.session_state.learner_state = updated_state
                st.session_state.bandit = updated_bandit
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": result["ai_reply"],
                        "feedback": result["feedback"],
                        "points": result["points"],
                        "total_points": result["total_points"],
                        "difficulty": result["difficulty"],
                        "profile": result["profile"],
                        "bandit": result["bandit"],
                        "llm_error": result.get("llm_error"),
                    }
                )
                st.rerun()


def render_video_call() -> None:
    render_page_intro(
        "Live AI practice",
        "Video call with Luna",
        (
            "Turn on your camera and microphone for a face-to-face practice "
            "experience. Use the live transcript box for the sentence you say, "
            "and Luna will respond with the same adaptive AI, feedback, and points."
        ),
    )

    state: LearnerState = st.session_state.learner_state

    settings_one, settings_two, settings_three, settings_four = st.columns(
        [1.1, 0.95, 0.9, 0.9], gap="small"
    )
    with settings_one:
        target_language = st.selectbox(
            "Target language",
            SUPPORTED_LANGUAGES,
            index=(
                SUPPORTED_LANGUAGES.index(state.target_language)
                if state.target_language in SUPPORTED_LANGUAGES
                else 0
            ),
            key="video_target_language_widget",
        )
    with settings_two:
        difficulty = st.selectbox(
            "Call level",
            DIFFICULTY_LEVELS,
            index=(
                DIFFICULTY_LEVELS.index(state.difficulty)
                if state.difficulty in DIFFICULTY_LEVELS
                else 0
            ),
            key="video_difficulty_widget",
        )
    with settings_three:
        auto_adapt = st.toggle(
            "Adaptive level",
            value=True,
            key="video_auto_adapt_widget",
            help="Let the epsilon-greedy bandit adapt the difficulty after each turn.",
        )
    with settings_four:
        use_llm = st.toggle(
            "Local LLM",
            value=False,
            key="video_use_llm_widget",
            help=f"Optional {MODEL_NAME} mode; the fast fallback works without it.",
        )

    state.target_language = target_language

    ai_col, self_col = st.columns([0.64, 0.36], gap="large", vertical_alignment="top")

    webrtc_ctx = None
    with self_col:
        with st.container(key="video-self-card"):
            st.markdown("### Your camera")
            st.caption("Allow camera + microphone access, then press START.")
            if WEBRTC_AVAILABLE and webrtc_streamer is not None and WebRtcMode is not None:
                webrtc_ctx = webrtc_streamer(
                    key="lingglot-video-call-media",
                    mode=WebRtcMode.SENDONLY,
                    rtc_configuration=build_rtc_configuration(),
                    media_stream_constraints={
                        "video": {
                            "width": {"ideal": 640},
                            "height": {"ideal": 480},
                            "facingMode": "user",
                        },
                        "audio": True,
                    },
                    media_toggle_controls=True,
                    video_html_attrs={
                        "autoPlay": True,
                        "controls": False,
                        "muted": True,
                        "playsInline": True,
                    },
                )
            else:
                st.warning(
                    "Live WebRTC is not installed in this environment. "
                    "A camera snapshot fallback is available below."
                )
                st.camera_input("Camera preview", key="video-camera-fallback")

            st.caption(
                "Media is used for the live session and is not saved by the "
                "Lingglot app. Browser/device permissions control camera and mic access."
            )

    is_live = bool(webrtc_ctx is not None and webrtc_ctx.state.playing)
    with ai_col:
        with st.container(key="video-call-stage"):
            st.html(
                video_call_stage_html(
                    target_language=target_language,
                    difficulty=difficulty,
                    is_live=is_live,
                    last_reply=str(st.session_state.video_last_reply),
                )
            )
            st.html(
                video_call_status_html(
                    camera_live=is_live,
                    target_language=target_language,
                    difficulty=difficulty,
                )
            )
            render_browser_tts(
                str(st.session_state.video_last_reply),
                target_language,
            )

    st.write("")
    transcript_col, coach_col = st.columns([0.62, 0.38], gap="large", vertical_alignment="top")

    with transcript_col:
        with st.container(key="video-call-transcript"):
            st.markdown("### Live conversation transcript")
            st.caption(
                "For the zero-API deployment, type the sentence you said aloud. "
                "Luna processes it immediately through the same language guard, "
                "adaptive learning engine, and scoring pipeline."
            )
            with st.container(height=360, key="video-transcript-scroll", border=False, autoscroll=True):
                for message in st.session_state.video_messages:
                    avatar = str(LUNA_IMAGE) if message["role"] == "assistant" else None
                    with st.chat_message(message["role"], avatar=avatar):
                        st.markdown(str(message.get("content", "")))
                        if message.get("feedback"):
                            render_feedback_card(message)

            transcript = st.chat_input(
                f"Type what you said in {target_language}...",
                key="video-transcript-input",
                max_chars=1200,
            )
            if transcript:
                with st.spinner("Luna is responding to your call..."):
                    submit_video_call_turn(
                        transcript,
                        target_language,
                        difficulty,
                        auto_adapt=auto_adapt,
                        use_llm=use_llm,
                    )
                st.rerun()

    with coach_col:
        with st.container(key="video-call-coach"):
            st.markdown("### Voice turn")
            st.caption(
                "Record a short voice note at speech-recognition quality. "
                "You can replay it, then enter its transcript in the call box."
            )
            voice_note = st.audio_input(
                "Record your sentence",
                sample_rate=16000,
                key="video_voice_note",
                width="stretch",
            )
            if voice_note is not None:
                st.success("Voice turn captured. Replay it above, then submit the transcript.")

            st.markdown("#### Call coaching")
            st.html(
                pills_html(
                    [
                        "Camera live" if is_live else "Camera ready",
                        target_language,
                        "Adaptive" if auto_adapt else difficulty,
                    ]
                )
            )
            st.markdown(
                """
- Keep each turn to one or two natural sentences.
- Look toward the camera while speaking.
- Use Luna's **Hear Luna** button for spoken pronunciation.
- Camera and microphone can be toggled from the WebRTC controls.
"""
            )

            if st.button(
                "Clear video-call transcript",
                icon=":material/refresh:",
                width="stretch",
                key="clear-video-call",
            ):
                st.session_state.video_messages = [
                    {
                        "role": "assistant",
                        "content": (
                            "Hi! I am Luna. Start your camera and microphone, then "
                            "practice with me in your target language."
                        ),
                    }
                ]
                st.session_state.video_last_reply = (
                    "Start the camera, then say or type a sentence to begin."
                )
                st.rerun()

    st.info(
        "Cloud note: WebRTC uses a public STUN server by default. Some corporate, "
        "school, or restrictive networks may also require a TURN relay. Optional "
        "TURN_URL, TURN_USERNAME, and TURN_CREDENTIAL secrets are supported.",
        icon=":material/cloud:",
    )



def sync_game_settings(state: LearnerState) -> tuple[str, str]:
    top_one, top_two = st.columns(2, gap="small")
    with top_one:
        target_language = st.selectbox(
            "Game language",
            SUPPORTED_LANGUAGES,
            index=(
                SUPPORTED_LANGUAGES.index(state.target_language)
                if state.target_language in SUPPORTED_LANGUAGES
                else 1
            ),
            key="games_language_widget",
        )
    with top_two:
        difficulty = st.selectbox(
            "Challenge level",
            DIFFICULTY_LEVELS,
            index=(
                DIFFICULTY_LEVELS.index(state.difficulty)
                if state.difficulty in DIFFICULTY_LEVELS
                else 0
            ),
            key="games_difficulty_widget",
        )

    if target_language != state.target_language:
        state.target_language = target_language
        st.session_state.pop("target_language_widget", None)
    if difficulty != state.difficulty:
        state.difficulty = difficulty
        st.session_state.pop("manual_difficulty_widget", None)
    return target_language, difficulty


def render_games() -> None:
    render_page_intro(
        "Mini-games",
        "Practice that plays like a game",
        (
            "Use short challenges to build vocabulary, rehearse real-life "
            "situations, and stretch sentence length without losing the flow."
        ),
    )
    state: LearnerState = st.session_state.learner_state
    target_language, difficulty = sync_game_settings(state)

    vocab_tab, roleplay_tab, expansion_tab = st.tabs(
        ["Vocabulary quiz", "Role-play", "Sentence expansion"]
    )

    with vocab_tab:
        with st.container(key="game-vocab"):
            st.markdown("### Vocabulary quiz")
            st.caption("Translate one useful word and earn 15 points.")
            st.html(
                f'<div class="game-prompt">{escape(st.session_state.current_vocab_question)}</div>'
            )

            if st.button(
                "Generate a new word",
                type="primary",
                icon=":material/casino:",
                key="generate-vocab-question",
            ):
                question, answer = generate_vocab_question(target_language)
                st.session_state.current_vocab_question = question
                st.session_state.current_vocab_answer = answer
                st.session_state.vocab_scored = False
                st.session_state.pop("vocab_answer_input", None)
                st.rerun()

            vocab_answer = st.text_input(
                "Your answer",
                key="vocab_answer_input",
                placeholder=f"Type the {target_language} translation",
            )
            if st.button(
                "Check answer",
                icon=":material/check_circle:",
                key="check-vocab-answer",
            ):
                correct_answer = st.session_state.current_vocab_answer
                if not correct_answer:
                    st.warning("Generate a vocabulary question first.")
                else:
                    is_correct, message = check_vocab_answer(
                        vocab_answer,
                        correct_answer,
                    )
                    if is_correct and not st.session_state.vocab_scored:
                        state.total_points += 15
                        state.mini_game_wins += 1
                        st.session_state.vocab_scored = True
                        st.success(
                            f"{message} Total points: {state.total_points}"
                        )
                    elif is_correct:
                        st.info(
                            "Correct. This question has already awarded its points."
                        )
                    else:
                        st.info(message)

    with roleplay_tab:
        with st.container(key="game-roleplay"):
            st.markdown("### Role-play")
            st.caption("Rehearse a practical situation at your current level.")
            st.html(
                f'<div class="game-prompt">{escape(st.session_state.roleplay_prompt)}</div>'
            )
            if st.button(
                "Generate a scenario",
                type="primary",
                icon=":material/theater_comedy:",
                key="generate-roleplay",
            ):
                st.session_state.roleplay_prompt = generate_roleplay_prompt(
                    target_language,
                    difficulty,
                )
                st.rerun()

            roleplay_draft = st.text_area(
                "Draft your response",
                key="roleplay_draft",
                height=130,
                placeholder="Write one sentence for the scenario...",
            )
            if st.button(
                "Continue this in Conversation",
                icon=":material/forum:",
                key="roleplay-to-chat",
            ):
                prompt = st.session_state.roleplay_prompt
                if roleplay_draft.strip():
                    prompt = f"{prompt} My draft: {roleplay_draft.strip()}"
                st.session_state.pending_challenge = prompt
                st.switch_page(PRACTICE_PAGE)

    with expansion_tab:
        with st.container(key="game-expansion"):
            st.markdown("### Sentence expansion")
            st.caption("Add emotion, time, and a reason to build fluency.")
            st.html(
                f'<div class="game-prompt">{escape(st.session_state.sentence_prompt)}</div>'
            )
            if st.button(
                "Generate a challenge",
                type="primary",
                icon=":material/auto_awesome:",
                key="generate-sentence-challenge",
            ):
                st.session_state.sentence_prompt = sentence_expansion_challenge(
                    target_language
                )
                st.rerun()

            sentence_draft = st.text_area(
                "Try the expanded sentence",
                key="sentence_draft",
                height=130,
                placeholder="Write a longer sentence...",
            )
            if st.button(
                "Ask Luna for feedback",
                icon=":material/forum:",
                key="sentence-to-chat",
            ):
                prompt = st.session_state.sentence_prompt
                if sentence_draft.strip():
                    prompt = f"{prompt} My draft: {sentence_draft.strip()}"
                st.session_state.pending_challenge = prompt
                st.switch_page(PRACTICE_PAGE)


def build_progress_tip(scores: Dict[str, int]) -> tuple[str, str]:
    lowest_skill = min(scores, key=scores.get)
    tips = {
        "Fluency": (
            "Build longer turns",
            "Try answering Luna with one extra detail and one follow-up question.",
        ),
        "Accuracy": (
            "Slow down for accuracy",
            "Review the tutor feedback and rewrite one corrected sentence aloud.",
        ),
        "Vocabulary": (
            "Add useful words",
            "Play two vocabulary rounds, then use both words in Conversation.",
        ),
        "Consistency": (
            "Create a short streak",
            "A few brief sessions are more useful than one very long session.",
        ),
        "Confidence": (
            "Choose a comfortable topic",
            "Start with a familiar topic and gradually increase the challenge level.",
        ),
    }
    return tips[lowest_skill]


def render_progress() -> None:
    render_page_intro(
        "AI progress",
        "See your speaking level up",
        (
            "Your session data powers visual skill estimates, learner clustering, "
            "adaptive-difficulty values, and a downloadable practice history."
        ),
    )
    state: LearnerState = st.session_state.learner_state
    profile = predict_learner_profile(state)
    scores = calculate_skill_scores(state)
    overall = round(sum(scores.values()) / len(scores))
    turns = max(state.conversation_turns, 1)

    with st.container(key="progress-overview"):
        top_left, top_right = st.columns([0.68, 0.32], gap="large")
        with top_left:
            st.markdown("### Current learner profile")
            st.markdown(f"**{profile}**")
            st.caption(
                "This label comes from the original scikit-learn KMeans model "
                "trained on synthetic learner profiles."
            )
        with top_right:
            st.metric("Overall session score", overall, help="Average of five session indicators")

        metric_cols = st.columns(4, gap="small")
        metric_cols[0].metric("Total points", state.total_points)
        metric_cols[1].metric("Conversation turns", state.conversation_turns)
        metric_cols[2].metric(
            "Average words / turn",
            round(state.total_words / turns, 1),
        )
        metric_cols[3].metric("Mini-game wins", state.mini_game_wins)

        st.markdown("### Skill indicators")
        score_cols = st.columns(2, gap="large")
        for index, (skill, value) in enumerate(scores.items()):
            with score_cols[index % 2]:
                st.write(f"**{skill}** - {value}%")
                st.progress(value)

        tip_title, tip_text = build_progress_tip(scores)
        st.html(progress_tip_html(tip_title, tip_text))

    st.write("")
    with st.container(key="progress-details"):
        history_tab, adaptive_tab, model_tab = st.tabs(
            ["Practice history", "Adaptive difficulty", "Clustering model"]
        )

        history_df = learner_history_dataframe(state)
        with history_tab:
            if history_df.empty:
                st.info(
                    "No practice history yet. Complete a conversation turn to "
                    "populate this dashboard."
                )
            else:
                chart_df = history_df[["points"]].copy()
                chart_df["Cumulative points"] = chart_df["points"].cumsum()
                chart_df.index = range(1, len(chart_df) + 1)
                st.line_chart(chart_df[["Cumulative points"]])
                st.dataframe(
                    history_df,
                    width="stretch",
                    hide_index=True,
                )

            csv = history_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download practice history CSV",
                data=csv,
                file_name="lingglot_practice_history.csv",
                mime="text/csv",
                disabled=history_df.empty,
                icon=":material/download:",
            )

        with adaptive_tab:
            bandit_summary = st.session_state.bandit.summary()
            adaptive_df = pd.DataFrame(
                {
                    "Difficulty": DIFFICULTY_LEVELS,
                    "Times selected": [
                        bandit_summary["counts"].get(level, 0)
                        for level in DIFFICULTY_LEVELS
                    ],
                    "Estimated reward": [
                        bandit_summary["estimated_values"].get(level, 0)
                        for level in DIFFICULTY_LEVELS
                    ],
                }
            )
            st.dataframe(adaptive_df, width="stretch", hide_index=True)
            st.caption(
                "The epsilon-greedy bandit balances exploration with the level "
                "that has produced the strongest reward estimate."
            )
            st.json(bandit_summary)

        with model_tab:
            _scaler, _kmeans, cluster_summary, cluster_labels = build_profile_model()
            st.dataframe(cluster_summary, width="stretch")
            st.json({int(key): value for key, value in cluster_labels.items()})
            st.caption(
                "The clustering data is synthetic and intended for prototype "
                "demonstration rather than formal language assessment."
            )


def render_about() -> None:
    render_page_intro(
        "About the integration",
        "Lovable design, Streamlit intelligence",
        (
            "This repository translates the supplied Lovable React/Tailwind "
            "visual system into native Streamlit while preserving the supplied "
            "Python learning algorithms."
        ),
    )

    with st.container(key="about-card"):
        st.markdown("### What is included")
        st.markdown(
            """
- Lovable-inspired cream, coral, and magenta theme with gradient highlights
- Fraunces display typography and Plus Jakarta Sans body typography
- Responsive landing page, procedural character art, cards, phone mockup, and animations
- AI character conversation with tutor feedback and reward points
- Live camera + microphone video-call practice with Luna through WebRTC
- Browser text-to-speech playback for Luna in all supported languages
- Optional local Hugging Face model mode using `google/flan-t5-small`
- Vocabulary, role-play, and sentence-expansion mini-games
- Epsilon-greedy adaptive difficulty selection
- Scikit-learn learner-profile clustering
- Session analytics and CSV history download
"""
        )

        st.markdown("### Application architecture")
        st.html(
            """
<div class="about-architecture">
  <div class="arch-step"><b>1. Streamlit interface</b><span>Navigation, chat, WebRTC video call, voice capture, mini-games, analytics, and responsive visual components.</span></div>
  <div class="arch-step"><b>2. Python learning core</b><span>Conversation prompts, feedback, rewards, language guard, bandit, and clustering logic.</span></div>
  <div class="arch-step"><b>3. Optional model layer</b><span>Local Hugging Face generation when the full requirements are installed; otherwise a fast fallback.</span></div>
</div>
"""
        )

        st.markdown("### Project credits")
        credit_one, credit_two, credit_three = st.columns(3, gap="small")
        credit_one.metric("Author", AUTHOR)
        credit_two.metric("Mentor", MENTOR)
        credit_three.metric("Advisor", ADVISOR)

        st.markdown("### Deploy on Streamlit Community Cloud")
        st.code(
            "Main file path: streamlit_app.py\n"
            "Install file: requirements.txt\n"
            "Optional model packages: requirements-full.txt",
            language="text",
        )
        st.info(
            "The default deployment does not require API keys or secrets. "
            "Do not commit a .streamlit/secrets.toml file to GitHub."
        )


initialize_session_state()

HOME_PAGE = st.Page(
    render_home,
    title="Home",
    icon=":material/home:",
    default=True,
)
PRACTICE_PAGE = st.Page(
    render_practice,
    title="Conversation",
    icon=":material/forum:",
    url_path="conversation",
)
VIDEO_CALL_PAGE = st.Page(
    render_video_call,
    title="Video call",
    icon=":material/video_call:",
    url_path="video-call",
)
GAMES_PAGE = st.Page(
    render_games,
    title="Mini-games",
    icon=":material/sports_esports:",
    url_path="mini-games",
)
PROGRESS_PAGE = st.Page(
    render_progress,
    title="Progress",
    icon=":material/insights:",
    url_path="progress",
)
ABOUT_PAGE = st.Page(
    render_about,
    title="About",
    icon=":material/info:",
    url_path="about",
)

navigation = st.navigation(
    [HOME_PAGE, PRACTICE_PAGE, VIDEO_CALL_PAGE, GAMES_PAGE, PROGRESS_PAGE, ABOUT_PAGE],
    position="top",
    expanded=True,
)
navigation.run()
