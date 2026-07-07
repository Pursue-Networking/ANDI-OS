"""Deterministic noise rules. Layer 1 of the noise detection system.

Pure functions, no database, no LLM, fully unit-testable. This is the main
extension surface for the noise / sender validation work:

  - add a feature: extend extract_envelope_features
  - tune a weight: edit WEIGHTS
  - move a boundary: edit NOISE_THRESHOLD / REAL_THRESHOLD

Anything the rules cannot decide lands in 'uncertain' and is passed to the
LLM triage agent (layer 2). Human labels (layer 3) always win.
"""

from __future__ import annotations

MARKETING_WORDS = [
    "unsubscribe", "limited time", "last chance", "exclusive deal", "% off",
    "book a demo", "webinar", "sale ends", "act now", "free trial", "10x",
    "special offer", "discount", "buy now",
]

NOREPLY_LOCALS = [
    "no-reply", "noreply", "do-not-reply", "donotreply", "notifications",
    "notification", "alerts", "alert", "digest", "newsletter", "updates",
    "mailer", "automated", "robot", "bounce",
]

TRANSACTIONAL_LOCALS = [
    "receipts", "receipt", "billing", "invoice", "invoices", "support",
    "help", "orders", "payments", "calendar-notification",
]

BULK_MAILERS = ["mailchimp", "sendgrid", "mailgun", "hubspot", "marketo", "braze", "klaviyo"]

# Score starts at 0.5. Noise evidence pushes up, human evidence pushes down.
WEIGHTS = {
    "auto_submitted": 0.35,
    "noreply_sender": 0.25,
    "has_list_unsubscribe": 0.25,
    "precedence_bulk": 0.20,
    "transactional_sender": 0.20,
    "bulk_mailer": 0.15,
    "marketing_subject": 0.15,
    "contains_unsubscribe_text": 0.10,
    "many_recipients": 0.10,
    "prior_outbound_to_sender": -0.40,
    "sender_in_linkedin": -0.30,
    "is_reply_in_thread": -0.20,
    "user_first_name_in_body": -0.15,
}

NOISE_THRESHOLD = 0.75  # score >= this -> noise
REAL_THRESHOLD = 0.30   # score <= this -> real, in between -> uncertain


def _local_part(email: str) -> str:
    return email.split("@", 1)[0].lower() if email else ""


def extract_envelope_features(email: dict, ctx: dict | None = None) -> dict:
    """Compute noise features for one raw email.

    email: a raw_emails row as dict (headers, from_email, subject, body_text,
           to_emails, cc_emails, in_reply_to, subject).
    ctx:   optional user context:
           user_first_name (str), linkedin_emails (set), outbound_recipients (set)
    """
    ctx = ctx or {}
    headers = {str(k).lower(): str(v).lower() for k, v in (email.get("headers") or {}).items()}
    from_email = (email.get("from_email") or "").lower()
    local = _local_part(from_email)
    subject = (email.get("subject") or "").lower()
    body = (email.get("body_text") or "").lower()
    text = subject + " " + body

    first_name = str(ctx.get("user_first_name") or "").lower()
    linkedin_emails = {e.lower() for e in ctx.get("linkedin_emails") or set()}
    outbound = {e.lower() for e in ctx.get("outbound_recipients") or set()}

    marketing_hits = [w for w in MARKETING_WORDS if w in text]
    recipients = len(email.get("to_emails") or []) + len(email.get("cc_emails") or [])

    return {
        "has_list_unsubscribe": "list-unsubscribe" in headers,
        "precedence_bulk": headers.get("precedence", "") in ("bulk", "list", "junk"),
        "auto_submitted": headers.get("auto-submitted", "no") not in ("", "no"),
        "noreply_sender": any(p in local for p in NOREPLY_LOCALS),
        "transactional_sender": any(p in local for p in TRANSACTIONAL_LOCALS),
        "bulk_mailer": any(m in headers.get("x-mailer", "") for m in BULK_MAILERS) or "feedback-id" in headers,
        "marketing_subject": len(marketing_hits) >= 2,
        "contains_unsubscribe_text": "unsubscribe" in body,
        "many_recipients": recipients > 10,
        "recipient_count": recipients,
        "marketing_hits": marketing_hits,
        "is_reply_in_thread": bool(email.get("in_reply_to")) or subject.startswith("re:"),
        "user_first_name_in_body": bool(first_name) and first_name in body,
        "sender_in_linkedin": from_email in linkedin_emails,
        "prior_outbound_to_sender": from_email in outbound,
    }


def rule_score(features: dict) -> tuple[float, str, list[str]]:
    """Turn features into (score 0..1, verdict, fired reasons).

    0.0 = surely a real human, 1.0 = surely noise.
    """
    score = 0.5
    reasons: list[str] = []
    for name, weight in WEIGHTS.items():
        if features.get(name):
            score += weight
            reasons.append(name)
    score = max(0.0, min(1.0, round(score, 3)))
    if score >= NOISE_THRESHOLD:
        verdict = "noise"
    elif score <= REAL_THRESHOLD:
        verdict = "real"
    else:
        verdict = "uncertain"
    return score, verdict, reasons
