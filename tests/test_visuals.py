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
