from lingglot.visuals import progress_stat_strip_html


def test_progress_stat_strip_renders_progress_and_other_stats():
    html = progress_stat_strip_html(
        23,
        {
            "Conversation turns": 1,
            "Current level": "Beginner",
            "Learner profile": "Consistent conversational learner",
        },
    )
    assert 'aria-valuenow="23"' in html
    assert 'style="width:23%"' in html
    assert "Practice progress" in html
    assert "Conversation turns" in html
    assert "Total points" not in html


def test_progress_stat_strip_clamps_percent():
    assert 'aria-valuenow="100"' in progress_stat_strip_html(145, {})
    assert 'aria-valuenow="0"' in progress_stat_strip_html(-8, {})

from lingglot.visuals import video_call_stage_html, video_call_status_html


def test_video_call_stage_renders_live_state_and_escapes_reply():
    html = video_call_stage_html(
        target_language="Spanish",
        difficulty="Intermediate",
        is_live=True,
        last_reply='<script>alert("x")</script> Hola',
    )
    assert "video-call-ai-stage is-live" in html
    assert "Spanish · Intermediate" in html
    assert "&lt;script&gt;" in html
    assert '<script>alert("x")</script>' not in html
    assert "LIVE" in html


def test_video_call_status_changes_with_connection_state():
    live = video_call_status_html(
        camera_live=True,
        target_language="French",
        difficulty="Beginner",
    )
    ready = video_call_status_html(
        camera_live=False,
        target_language="French",
        difficulty="Beginner",
    )
    assert "Camera + mic: Connected" in live
    assert "Camera + mic: Ready to connect" in ready
    assert "Practice: French" in live
