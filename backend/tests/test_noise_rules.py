"""Unit tests for the deterministic noise rules. No database, no network."""

from backend.app.noise.rules import extract_envelope_features, rule_score

CTX = {
    "user_first_name": "Bhuvnesh",
    "linkedin_emails": {"kolin@roswellventures.com"},
    "outbound_recipients": {"kolin@roswellventures.com"},
}


def _email(**overrides) -> dict:
    base = {
        "from_email": "someone@example.com",
        "from_name": "Someone",
        "subject": "hello",
        "body_text": "hello",
        "to_emails": ["bhuvnesh@andi.local"],
        "cc_emails": [],
        "headers": {},
        "in_reply_to": "",
    }
    base.update(overrides)
    return base


def test_newsletter_is_noise():
    email = _email(
        from_email="digest@mail.startupdigest.com",
        subject="Your weekly startup digest #214",
        body_text="This week in startups. Unsubscribe at any time.",
        headers={"List-Unsubscribe": "<mailto:unsub@x>", "Precedence": "bulk"},
    )
    score, verdict, reasons = rule_score(extract_envelope_features(email, CTX))
    assert verdict == "noise"
    assert score >= 0.75
    assert "has_list_unsubscribe" in reasons


def test_known_human_reply_is_real():
    email = _email(
        from_email="kolin@roswellventures.com",
        subject="Re: Revised scope",
        body_text="Hi Bhuvnesh, can you send the budget split?",
        in_reply_to="<msg-1@mail>",
    )
    score, verdict, reasons = rule_score(extract_envelope_features(email, CTX))
    assert verdict == "real"
    assert score <= 0.30
    assert "prior_outbound_to_sender" in reasons


def test_personalized_cold_email_is_uncertain():
    email = _email(
        from_email="jordan@pipelineiq.io",
        subject="Your take on relationship-first outreach",
        body_text="Hi Bhuvnesh, read your post. Open to comparing notes?",
    )
    score, verdict, _ = rule_score(extract_envelope_features(email, CTX))
    assert verdict == "uncertain"
    assert 0.30 < score < 0.75


def test_auto_submitted_bot_is_noise():
    email = _email(
        from_email="notifications@github.com",
        subject="[repo] Run failed",
        body_text="Run failed for dev.",
        headers={"Auto-Submitted": "auto-generated", "Precedence": "list"},
    )
    _, verdict, reasons = rule_score(extract_envelope_features(email, CTX))
    assert verdict == "noise"
    assert "auto_submitted" in reasons
    assert "noreply_sender" in reasons


def test_empty_email_does_not_crash_and_score_is_bounded():
    features = extract_envelope_features({}, None)
    score, verdict, _ = rule_score(features)
    assert 0.0 <= score <= 1.0
    assert verdict in ("real", "noise", "uncertain")


def test_features_contain_documented_keys():
    features = extract_envelope_features(_email(), CTX)
    for key in (
        "has_list_unsubscribe", "precedence_bulk", "auto_submitted", "noreply_sender",
        "transactional_sender", "bulk_mailer", "marketing_subject", "contains_unsubscribe_text",
        "many_recipients", "is_reply_in_thread", "user_first_name_in_body",
        "sender_in_linkedin", "prior_outbound_to_sender",
    ):
        assert key in features
