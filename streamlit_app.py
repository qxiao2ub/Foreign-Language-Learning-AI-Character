"""Lingglot: Lovable-inspired Streamlit interface with the original AI logic."""

from __future__ import annotations

from html import escape
from pathlib import Path
import re
import sys
from typing import Any, Dict

import pandas as pd
import streamlit as st
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
    ROOT / "lingglot" / "realtime_call.py",
    ROOT / "lingglot" / "elevenlabs_voice.py",
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
  realtime_call.py
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
from lingglot.realtime_call import mount_realtime_call
from lingglot.dictation import mount_dictation
from lingglot.elevenlabs_voice import (
    audio_data_uri,
    elevenlabs_configured,
    get_model_id,
    synthesize_elevenlabs,
)
from lingglot.visuals import (
    CHARACTERS,
    character_grid_html,
    character_svg,
    cta_banner_html,
    feature_grid_html,
    hero_phone_html,
    progress_tip_html,
    progress_stat_strip_html,
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


CHARACTER_OPTIONS = [name for name, _trait in CHARACTERS]
CHARACTER_INDEX = {name: i for i, name in enumerate(CHARACTER_OPTIONS)}
CHARACTER_VOICE_LABELS = {
    "Luna": "Warm tutor",
    "Milo": "Calm guide",
    "Pico": "Bright coach",
    "Nori": "Energetic coach",
    "Sol": "Thoughtful mentor",
    "Bibi": "Friendly companion",
}



VIDEO_CALL_COMPONENT_KEY = "lingglot_realtime_call"

VIDEO_CALL_GREETINGS = {
    "English": "Hello! I am Luna. Tell me one thing about your day.",
    "Spanish": "¡Hola! Soy Luna. Cuéntame una cosa sobre tu día.",
    "French": "Bonjour ! Je suis Luna. Raconte-moi une chose sur ta journée.",
    "German": "Hallo! Ich bin Luna. Erzähl mir eine Sache über deinen Tag.",
    "Italian": "Ciao! Sono Luna. Raccontami una cosa della tua giornata.",
    "Portuguese": "Olá! Eu sou a Luna. Conte-me uma coisa sobre o seu dia.",
    "Chinese": "你好！我是 Luna。请告诉我今天发生的一件事。",
    "Japanese": "こんにちは！ルナです。今日のことを一つ教えてください。",
    "Korean": "안녕하세요! 저는 루나예요. 오늘 있었던 일 한 가지를 말해 주세요.",
    "Arabic": "مرحبًا! أنا لونا. أخبرني بشيء واحد عن يومك.",
}


def submit_video_call_turn(
    transcript: str,
    target_language: str,
    difficulty: str,
    *,
    character_name: str = "Luna",
    auto_adapt: bool,
    use_llm: bool,
    source: str = "speech",
    event_id: str = "",
) -> Dict[str, Any] | None:
    """Run one finalized live transcript through the learning engine."""

    prompt = transcript.strip()[:1200]
    if not prompt:
        return None

    st.session_state.video_messages.append(
        {
            "role": "user",
            "content": prompt,
            "source": source,
            "event_id": event_id,
        }
    )
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
    st.session_state.video_last_reply = str(result["ai_reply"])
    st.session_state.video_voice_audio = ""
    st.session_state.video_voice_error = None
    # Natural AI voice is optional: the app continues to work with the browser
    # voice fallback when ElevenLabs is not configured.
    if elevenlabs_configured():
        try:
            audio_bytes = synthesize_elevenlabs(
                st.session_state.video_last_reply,
                language_code=LANGUAGE_VOICE_LOCALES.get(target_language, "en-US"),
                character=character_name,
            )
            st.session_state.video_voice_audio = audio_data_uri(audio_bytes)
        except Exception as exc:
            st.session_state.video_voice_error = str(exc)
    st.session_state.video_reply_id = int(
        st.session_state.get("video_reply_id", 0)
    ) + 1
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
            "event_id": event_id,
        }
    )
    return result


def _component_trigger_value(component_key: str, trigger_name: str) -> Any:
    """Read a Components V2 trigger from Session State safely."""

    component_state = st.session_state.get(component_key)
    if component_state is None:
        return None
    if isinstance(component_state, dict):
        return component_state.get(trigger_name)
    return getattr(component_state, trigger_name, None)


def handle_realtime_video_utterance() -> None:
    """Process one finalized browser speech-recognition turn."""

    event = _component_trigger_value(VIDEO_CALL_COMPONENT_KEY, "utterance")
    if not isinstance(event, dict):
        return

    event_id = str(event.get("id", "")).strip()
    if not event_id or event_id == st.session_state.get("video_last_event_id"):
        return

    # Mark the event before generation so an error cannot cause a duplicate turn.
    st.session_state.video_last_event_id = event_id
    st.session_state.video_processing_error = None

    transcript = str(event.get("text", "")).strip()[:1200]
    if not transcript:
        return

    state: LearnerState = st.session_state.learner_state
    target_language = str(
        st.session_state.get("video_target_language_widget", state.target_language)
    )
    if target_language not in SUPPORTED_LANGUAGES:
        target_language = state.target_language

    difficulty = str(
        st.session_state.get("video_difficulty_widget", state.difficulty)
    )
    if difficulty not in DIFFICULTY_LEVELS:
        difficulty = "Beginner"

    try:
        submit_video_call_turn(
            transcript,
            target_language,
            difficulty,
            character_name=str(st.session_state.get("character_name", "Luna")),
            auto_adapt=False,
            use_llm=False,
            source=str(event.get("source", "speech")),
            event_id=event_id,
        )
    except Exception as exc:  # pragma: no cover - deployment safety path
        st.session_state.video_processing_error = str(exc)


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
        "character_name": "Luna",
        "dictation_last_id": "",
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
        "video_last_reply": VIDEO_CALL_GREETINGS["English"],
        "video_reply_id": 0,
        "video_reset_token": 0,
        "video_last_event_id": "",
        "video_processing_error": None,
        "video_voice_audio": "",
        "video_voice_error": None,
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
        "character_widget",
        "video_character_widget",
        "manual_difficulty_widget",
        "composer_text",
        "dictation_component",
        "dictation_last_id",
        "games_language_widget",
        "games_difficulty_widget",
        "vocab_answer_input",
        "roleplay_draft",
        "sentence_draft",
        "video_messages",
        "video_last_reply",
        "video_reply_id",
        "video_reset_token",
        "video_last_event_id",
        "video_processing_error",
        "video_voice_audio",
        "video_voice_error",
        "character_name",
        VIDEO_CALL_COMPONENT_KEY,
        "video_target_language_widget",
        "video_difficulty_widget",
        "match_selection_left",
        "match_selection_right",
        "match_hits",
        "match_language",
        "matched_pairs",
        "listen_awarded",
        "picture_awarded",
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
    st.html(
        f"""
<div class="tutor-feedback-card">
  <strong>Tutor feedback</strong>
  <p>{feedback}</p>
  <div class="feedback-meta">
    <span>+{points} points</span>
  </div>
</div>
"""
    )


def _apply_character(character_name: str) -> None:
    if character_name not in CHARACTER_INDEX:
        character_name = "Luna"
    st.session_state.character_name = character_name


def _dictation_trigger_value() -> Any:
    state = st.session_state.get("dictation_component")
    if isinstance(state, dict):
        return state.get("dictation")
    return getattr(state, "dictation", None) if state is not None else None


def render_practice() -> None:
    state: LearnerState = st.session_state.learner_state
    settings_col, chat_col = st.columns([0.28, 0.72], gap="large", vertical_alignment="top")

    with settings_col:
        with st.container(key="practice-settings"):
            current_character = st.session_state.get("character_name", "Luna")
            character_name = st.selectbox(
                "Character",
                CHARACTER_OPTIONS,
                index=CHARACTER_OPTIONS.index(current_character) if current_character in CHARACTER_OPTIONS else 0,
                key="character_widget",
            )
            _apply_character(character_name)
            avatar_index = CHARACTER_INDEX.get(character_name, 0)
            st.html(
                f"""<div class='conversation-character-row'>{character_svg(avatar_index, size=54, id_prefix='conversation-sidebar')}<div><strong>{escape(character_name)}</strong><small>{escape(CHARACTER_VOICE_LABELS.get(character_name, 'Language partner'))}</small></div></div>"""
            )
            learner_name = st.text_input("Learner name", value=state.username, key="learner_name_widget")
            target_language = st.selectbox(
                "Target language",
                SUPPORTED_LANGUAGES,
                index=SUPPORTED_LANGUAGES.index(state.target_language) if state.target_language in SUPPORTED_LANGUAGES else 0,
                key="target_language_widget",
            )
            difficulty = st.selectbox(
                "Difficulty level",
                DIFFICULTY_LEVELS,
                index=DIFFICULTY_LEVELS.index(state.difficulty) if state.difficulty in DIFFICULTY_LEVELS else 0,
                key="manual_difficulty_widget",
            )
            state.username = learner_name
            state.target_language = target_language
            state.difficulty = difficulty
            st.caption("Your selected character keeps the same supportive personality across Conversation and Video call.")

    with chat_col:
        top_controls = st.columns([0.62, 0.19, 0.19], gap="small")
        with top_controls[0]:
            progress = min(100, max(0, state.total_points))
            st.html(
                progress_stat_strip_html(
                    progress,
                    {},
                    label="Practice progress",
                    helper="Toward your 100-point practice goal",
                )
            )
        with top_controls[1]:
            st.button("New chat", icon=":material/refresh:", width="stretch", key="clear-conversation-button", on_click=clear_conversation)
        with top_controls[2]:
            st.button("Reset all", icon=":material/restart_alt:", width="stretch", key="reset-all-button", on_click=reset_all_state)

        pending = st.session_state.get("pending_challenge")
        if pending:
            st.info(f"Practice prompt: {pending}", icon=":material/lightbulb:")
            if st.button("Dismiss", key="dismiss-pending-challenge", icon=":material/close:"):
                st.session_state.pending_challenge = None
                st.rerun()

        with st.container(key="practice-chat"):
            with st.container(height=560, key="chat-scroll", border=False, autoscroll=True):
                conversation_avatar = ASSET_DIR / "characters" / f"{character_name.lower()}.svg"
                for message in st.session_state.messages:
                    avatar = str(conversation_avatar) if message["role"] == "assistant" else None
                    with st.chat_message(message["role"], avatar=avatar):
                        st.markdown(str(message.get("content", "")))
                        if message.get("feedback"):
                            render_feedback_card(message)

            # Compact custom composer: microphone button sits beside the long input line.
            dictation_result = mount_dictation(
                locale=LANGUAGE_VOICE_LOCALES.get(target_language, "en-US"),
                key="lingglot_dictation_conversation",
            )
            st.session_state.dictation_component = dictation_result
            event = _dictation_trigger_value()
            if isinstance(event, dict) and event.get("id") != st.session_state.get("dictation_last_id"):
                st.session_state.dictation_last_id = str(event.get("id"))
                st.session_state.composer_text = str(event.get("text", "")).strip()

            composer_cols = st.columns([0.9, 0.1], gap="small", vertical_alignment="bottom")
            with composer_cols[0]:
                prompt = st.text_input(
                    "Message",
                    key="composer_text",
                    label_visibility="collapsed",
                    placeholder=f"Write or dictate something in {target_language}…",
                )
            with composer_cols[1]:
                send = st.button("Send", type="primary", width="stretch", key="composer_send", icon=":material/send:")

            if send and prompt.strip():
                st.session_state.messages.append({"role": "user", "content": prompt.strip()})
                with st.spinner(f"{character_name} is thinking…"):
                    result, updated_state, updated_bandit = language_learning_turn(
                        st.session_state.learner_state,
                        st.session_state.bandit,
                        prompt.strip(),
                        target_language,
                        difficulty,
                        auto_adapt_difficulty=False,
                        use_llm=False,
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
                    }
                )
                st.session_state.composer_text = ""
                st.rerun()


def render_video_call() -> None:
    render_page_intro(
        "Real-time AI practice",
        "Live video call with Luna",
        "See your camera live, speak naturally, watch the transcript build in real time, and receive a spoken reply in your selected learning language.",
    )
    state: LearnerState = st.session_state.learner_state

    top_one, top_two, top_three = st.columns([1.0, 1.0, 1.0], gap="small")
    with top_one:
        character_name = st.selectbox("Character", CHARACTER_OPTIONS, index=CHARACTER_OPTIONS.index(st.session_state.get("character_name", "Luna")), key="video_character_widget")
        _apply_character(character_name)
    with top_two:
        target_language = st.selectbox(
            "Target language",
            SUPPORTED_LANGUAGES,
            index=SUPPORTED_LANGUAGES.index(state.target_language) if state.target_language in SUPPORTED_LANGUAGES else 0,
            key="video_target_language_widget",
        )
    with top_three:
        difficulty = st.selectbox(
            "Difficulty level",
            DIFFICULTY_LEVELS,
            index=DIFFICULTY_LEVELS.index(state.difficulty) if state.difficulty in DIFFICULTY_LEVELS else 0,
            key="video_difficulty_widget",
        )

    state.target_language = target_language
    state.difficulty = difficulty
    selected_avatar = ASSET_DIR / "characters" / f"{character_name.lower()}.svg"
    voice_id_note = f"ELEVENLABS_{re.sub(r'[^A-Za-z0-9]+', '_', character_name).upper()}_VOICE_ID"

    greeting_templates = dict(VIDEO_CALL_GREETINGS)
    greeting = greeting_templates.get(target_language, greeting_templates["English"])
    if int(st.session_state.get("video_reply_id", 0)) == 0:
        st.session_state.video_last_reply = greeting
        if not any(message.get("role") == "user" for message in st.session_state.video_messages):
            st.session_state.video_messages = [{"role": "assistant", "content": greeting}]

    if elevenlabs_configured():
        st.success(
            f"Natural voice active for {character_name} using ElevenLabs. Optional character voice secret: `{voice_id_note}`.",
            icon=":material/graphic_eq:",
        )
    else:
        st.info(
            "Add ELEVENLABS_API_KEY to Streamlit Secrets for natural AI voices. The browser voice is used only as a fallback.",
            icon=":material/record_voice_over:",
        )

    if st.session_state.get("video_processing_error"):
        st.error(f"Luna could not process the last sentence: {st.session_state.video_processing_error}")

    with st.container(key="realtime-video-call-container"):
        mount_realtime_call(
            target_language=target_language,
            locale=LANGUAGE_VOICE_LOCALES.get(target_language, "en-US"),
            difficulty=difficulty,
            character_name=character_name,
            assistant_reply=str(st.session_state.video_last_reply),
            assistant_reply_id=int(st.session_state.video_reply_id),
            assistant_audio_data_uri=str(st.session_state.get("video_voice_audio", "")),
            voice_provider="ElevenLabs" if elevenlabs_configured() else "Browser voice fallback",
            history=st.session_state.video_messages,
            avatar_path=selected_avatar,
            reset_token=int(st.session_state.video_reset_token),
            key=VIDEO_CALL_COMPONENT_KEY,
            on_utterance=handle_realtime_video_utterance,
            height=1040,
        )

    st.html('<div class="computer-transcript-heading"><span class="eyebrow">CALL TRANSCRIPT</span><h2>Computer-generated transcript</h2><p>Every finalized sentence from the call is recorded here automatically.</p></div>')
    transcript_rows = []
    for message in st.session_state.video_messages:
        transcript_rows.append({
            "Speaker": "You" if message.get("role") == "user" else character_name,
            "Transcript": str(message.get("content", "")),
        })
    if transcript_rows:
        st.dataframe(pd.DataFrame(transcript_rows), width="stretch", hide_index=True)

    action_one, action_two = st.columns(2, gap="small")
    with action_one:
        if st.button("Clear call transcript", icon=":material/refresh:", width="stretch", key="clear-realtime-video-transcript"):
            st.session_state.video_messages = [{"role": "assistant", "content": greeting}]
            st.session_state.video_last_reply = greeting
            st.session_state.video_reply_id = 0
            st.session_state.video_last_event_id = ""
            st.session_state.video_processing_error = None
            st.session_state.video_voice_audio = ""
            st.session_state.video_voice_error = None
            st.session_state.video_reset_token = int(st.session_state.get("video_reset_token", 0)) + 1
            st.rerun()
    with action_two:
        if st.button("Reset all learning progress", icon=":material/restart_alt:", width="stretch", key="reset-from-realtime-video-call"):
            reset_all_state()
            st.rerun()


def sync_game_settings(state: LearnerState) -> tuple[str, str]:
    top_one, top_two = st.columns(2, gap="small")
    with top_one:
        target_language = st.selectbox(
            "Game language",
            SUPPORTED_LANGUAGES,
            index=SUPPORTED_LANGUAGES.index(state.target_language) if state.target_language in SUPPORTED_LANGUAGES else 1,
            key="games_language_widget",
        )
    with top_two:
        difficulty = st.selectbox(
            "Challenge level",
            DIFFICULTY_LEVELS,
            index=DIFFICULTY_LEVELS.index(state.difficulty) if state.difficulty in DIFFICULTY_LEVELS else 0,
            key="games_difficulty_widget",
        )
    state.target_language = target_language
    state.difficulty = difficulty
    return target_language, difficulty


def _game_vocab_pairs(language: str) -> list[tuple[str, str]]:
    banks = {
        "Spanish": [("manzana", "apple"), ("gato", "cat"), ("libro", "book"), ("agua", "water")],
        "French": [("pomme", "apple"), ("chat", "cat"), ("livre", "book"), ("eau", "water")],
        "German": [("apfel", "apple"), ("katze", "cat"), ("buch", "book"), ("wasser", "water")],
        "Italian": [("mela", "apple"), ("gatto", "cat"), ("libro", "book"), ("acqua", "water")],
        "Portuguese": [("maçã", "apple"), ("gato", "cat"), ("livro", "book"), ("água", "water")],
        "Chinese": [("苹果", "apple"), ("猫", "cat"), ("书", "book"), ("水", "water")],
        "Japanese": [("りんご", "apple"), ("ねこ", "cat"), ("本", "book"), ("水", "water")],
        "Korean": [("사과", "apple"), ("고양이", "cat"), ("책", "book"), ("물", "water")],
        "Arabic": [("تفاحة", "apple"), ("قطة", "cat"), ("كتاب", "book"), ("ماء", "water")],
        "English": [("apple", "apple"), ("cat", "cat"), ("book", "book"), ("water", "water")],
    }
    return banks.get(language, banks["Spanish"])


def _browser_speak_html(text: str, locale: str) -> str:
    safe_text = escape(text).replace("\\", "\\\\").replace("'", "\\'")
    safe_locale = escape(locale)
    return f"""<button class=\\"listen-demo-button\\" onclick=\\"(function(){{const u=new SpeechSynthesisUtterance('{safe_text}');u.lang='{safe_locale}';u.rate=.9;window.speechSynthesis.cancel();window.speechSynthesis.speak(u);}})()\\">▶ Play phrase</button>"""


def render_games() -> None:
    render_page_intro("Mini-games", "Practice that plays like a game", "Small, focused challenges inspired by the Lovable demo: match words, listen and choose, and connect a word to the right picture.")
    state = st.session_state.learner_state
    target_language, difficulty = sync_game_settings(state)

    match_tab, listening_tab, picture_tab = st.tabs(["Word match", "Listening challenge", "Word-to-picture"])

    pairs = _game_vocab_pairs(target_language)
    with match_tab:
        with st.container(key="game-word-match"):
            st.markdown("### Word match")
            st.caption("Connect each target-language word with its meaning.")
            if "match_selection_left" not in st.session_state or st.session_state.get("match_language") != target_language:
                st.session_state.match_selection_left = None
                st.session_state.match_selection_right = None
                st.session_state.match_hits = 0
                st.session_state.match_language = target_language
                st.session_state.matched_pairs = set()
            left_col, right_col = st.columns(2, gap="medium")
            left_words = [a for a, _ in pairs]
            right_words = [b for _, b in reversed(pairs)]
            with left_col:
                st.caption(f"{target_language}")
                for idx, word in enumerate(left_words):
                    if st.button(word, key=f"match-left-{target_language}-{idx}", width="stretch"):
                        st.session_state.match_selection_left = word
            with right_col:
                st.caption("Meaning")
                for idx, word in enumerate(right_words):
                    if st.button(word, key=f"match-right-{target_language}-{idx}", width="stretch"):
                        st.session_state.match_selection_right = word
            if st.session_state.get("match_selection_left") and st.session_state.get("match_selection_right"):
                selected_left = st.session_state.match_selection_left
                selected_right = st.session_state.match_selection_right
                lookup = dict(pairs)
                if lookup.get(selected_left) == selected_right:
                    pair_key = (selected_left, selected_right)
                    matched_pairs = st.session_state.get("matched_pairs", set())
                    if pair_key not in matched_pairs:
                        matched_pairs.add(pair_key)
                        st.session_state.matched_pairs = matched_pairs
                        st.session_state.match_hits += 1
                        state.total_points += 5
                        state.mini_game_wins += 1
                    st.success("Match! +5 points")
                else:
                    st.warning("Not a match yet — try another pair.")
            st.progress(min(1.0, st.session_state.get("match_hits", 0) / len(pairs)), text=f"{st.session_state.get('match_hits', 0)} / {len(pairs)} matched")

    with listening_tab:
        with st.container(key="game-listening-challenge"):
            st.markdown("### Listening challenge")
            st.caption("Play a phrase, then choose what you heard.")
            listen_content = {
                "English": ("Good morning, how are you?", ["Good morning, how are you?", "Good evening, where are you?", "Nice to meet you tomorrow.", "How old is your brother?"]),
                "Spanish": ("¿Dónde está la estación?", ["¿Dónde está la estación?", "¿Dónde está el café?", "¿Cómo está la escuela?", "¿Cuándo es la fiesta?"]),
                "French": ("Où est la gare ?", ["Où est la gare ?", "Où est la rue ?", "Où est le café ?", "Où est l'école ?"]),
                "German": ("Wo ist der Bahnhof?", ["Wo ist der Bahnhof?", "Wo ist das Hotel?", "Wie geht es dir?", "Was ist das Buch?"]),
                "Italian": ("Dov'è la stazione?", ["Dov'è la stazione?", "Dov'è il museo?", "Come stai oggi?", "Quando parte il treno?"]),
                "Portuguese": ("Onde fica a estação?", ["Onde fica a estação?", "Onde fica o hotel?", "Como está o café?", "Quando começa a aula?"]),
                "Chinese": ("车站在哪里？", ["车站在哪里？", "学校在哪里？", "你叫什么名字？", "今天星期几？"]),
                "Japanese": ("駅はどこですか？", ["駅はどこですか？", "学校はどこですか？", "今日は何時ですか？", "お名前は何ですか？"]),
                "Korean": ("기차역이 어디예요?", ["기차역이 어디예요?", "학교가 어디예요?", "오늘 뭐 해요?", "이름이 뭐예요?"]),
                "Arabic": ("أين المحطة؟", ["أين المحطة؟", "أين المدرسة؟", "كيف حالك؟", "متى يبدأ الدرس؟"]),
            }
            phrase, choices = listen_content[target_language]
            st.html(_browser_speak_html(phrase, LANGUAGE_VOICE_LOCALES.get(target_language, "en-US")), unsafe_allow_javascript=True)
            selected = st.radio("What did you hear?", choices, key=f"listen-choice-{target_language}")
            if st.button("Check", type="primary", key="check-listen"):
                award_key = f"{target_language}:listening"
                if selected == phrase:
                    if st.session_state.get("listen_awarded") != award_key:
                        state.total_points += 5
                        state.mini_game_wins += 1
                        st.session_state.listen_awarded = award_key
                    st.success("Correct listening! +5 points")
                else:
                    st.info(f"Keep listening. The phrase was: {phrase}")

    with picture_tab:
        with st.container(key="game-picture-match"):
            st.markdown("### Word-to-picture match")
            st.caption("Choose the picture that matches the target-language word.")
            picture_bank = {
                "apple": "🍎", "cat": "🐈", "book": "📘", "water": "💧",
            }
            chosen_pair = pairs[0]
            word = chosen_pair[0]
            answer = chosen_pair[1]
            image_options = [answer] + [pair[1] for pair in pairs[1:]]
            shuffled = list(reversed(image_options))
            st.markdown(f"### {escape(word)}")
            pic_cols = st.columns(4, gap="small")
            for idx, meaning in enumerate(shuffled):
                with pic_cols[idx]:
                    emoji = picture_bank.get(meaning, "🖼️")
                    st.markdown(f"<div class='picture-choice'>{emoji}<span>{escape(meaning)}</span></div>", unsafe_allow_html=True)
                    if st.button("Choose", key=f"picture-{target_language}-{idx}", width="stretch"):
                        award_key = f"{target_language}:picture"
                        if meaning == answer:
                            if st.session_state.get("picture_awarded") != award_key:
                                state.total_points += 5
                                state.mini_game_wins += 1
                                st.session_state.picture_awarded = award_key
                            st.success("Correct picture! +5 points")
                        else:
                            st.warning("Try another picture.")


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
        "A cleaner snapshot of your 100-point learning journey, your strongest skills, and what to practice next.",
    )
    state: LearnerState = st.session_state.learner_state
    scores = calculate_skill_scores(state)
    overall = round(sum(scores.values()) / len(scores))
    points_progress = min(100, max(0, state.total_points))

    with st.container(key="progress-overview"):
        top_left, top_right = st.columns([0.74, 0.26], gap="large", vertical_alignment="center")
        with top_left:
            st.markdown("### Your 100-point journey")
            st.progress(points_progress / 100.0, text=f"{points_progress} / 100 points")
            st.caption("Points come from productive conversation turns and focused mini-game practice.")
        with top_right:
            st.metric("Overall skill", f"{overall}%")

        st.markdown("### Skill snapshot")
        skills = list(scores.items())
        skill_cols = st.columns(4, gap="small")
        for col, (skill, value) in zip(skill_cols, skills):
            with col:
                st.metric(skill, f"{value}%")
                st.progress(value / 100.0)

        st.markdown("### Practice summary")
        summary_cols = st.columns(3, gap="small")
        summary_cols[0].metric("Conversation turns", state.conversation_turns)
        summary_cols[1].metric("Words practiced", state.total_words)
        summary_cols[2].metric("Mini-game wins", state.mini_game_wins)

        tip_title, tip_text = build_progress_tip(scores)
        st.html(progress_tip_html(tip_title, tip_text))

    with st.container(key="progress-history"):
        st.markdown("### Recent practice")
        history_df = learner_history_dataframe(state)
        if history_df.empty:
            st.info("Complete a conversation turn or mini-game to see recent practice here.")
        else:
            recent = history_df.tail(8).copy()
            display_cols = [c for c in ["timestamp", "target_language", "difficulty", "points", "words", "feedback"] if c in recent.columns]
            st.dataframe(recent[display_cols], width="stretch", hide_index=True)
            st.caption("Only the most recent practice turns are shown to keep this page easy to scan.")


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
- Real-time browser camera + microphone preview through Streamlit Components V2
- Interim and final live speech transcript for every learner turn
- Automatic AI reply and browser text-to-speech in the selected target language
- Character selector with compact, Lovable-inspired partner cards
- Word match, listening challenge, and word-to-picture mini-games
- Real-time video call with automatic transcript processing and natural voice support
- 100-point progress journey with friendly skill snapshots
"""
        )

        st.markdown("### Application architecture")
        st.html(
            """
<div class="about-architecture">
  <div class="arch-step"><b>1. Streamlit interface</b><span>Navigation, chat, a Components V2 real-time camera/transcript call, mini-games, analytics, and responsive visual components.</span></div>
  <div class="arch-step"><b>2. Python learning core</b><span>Conversation prompts, feedback, rewards, language guard, bandit, and clustering logic.</span></div>
  <div class="arch-step"><b>3. Voice layer</b><span>ElevenLabs provides natural AI speech when configured; the browser remains a fallback.</span></div>
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
