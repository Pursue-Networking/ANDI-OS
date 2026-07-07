"""Dummy ingestion endpoints. They accept Gmail-shaped, Calendar-shaped and
LinkedIn-export-shaped JSON and land it in the RAW layer, deduplicated.
Swapping these for the real MCP-driven sync later does not change the schema.
"""

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .. import db
from .deps import default_user_id

router = APIRouter(prefix="/ingest", tags=["ingest"])


class GmailMessageIn(BaseModel):
    gmail_message_id: str
    gmail_thread_id: str
    from_email: str
    from_name: str = ""
    to_emails: list[str] = Field(default_factory=list)
    cc_emails: list[str] = Field(default_factory=list)
    subject: str = ""
    snippet: str = ""
    body_text: str = ""
    body_html: str = ""
    labels: list[str] = Field(default_factory=list)
    headers: dict[str, str] = Field(default_factory=dict)
    internal_date: datetime
    message_id_header: str = ""
    in_reply_to: str = ""


class GmailBatchIn(BaseModel):
    account_email: str
    messages: list[GmailMessageIn]


@router.post("/gmail")
def ingest_gmail(batch: GmailBatchIn, user_id: str = Depends(default_user_id)):
    account = db.q1(
        "SELECT id, email_address FROM email_accounts WHERE user_id = %s AND lower(email_address) = lower(%s)",
        (user_id, batch.account_email),
    )
    if not account:
        raise HTTPException(status_code=404, detail=f"no connected account {batch.account_email}")
    inserted = 0
    for m in batch.messages:
        direction = "outbound" if m.from_email.lower() == account["email_address"].lower() else "inbound"
        inserted += db.execute(
            """INSERT INTO raw_emails
               (user_id, account_id, gmail_message_id, gmail_thread_id, message_id_header, in_reply_to,
                direction, from_email, from_name, to_emails, cc_emails, subject, snippet, body_text,
                body_html, labels, headers, internal_date)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (account_id, gmail_message_id) DO NOTHING""",
            (
                user_id, account["id"], m.gmail_message_id, m.gmail_thread_id, m.message_id_header,
                m.in_reply_to, direction, m.from_email.lower(), m.from_name, m.to_emails, m.cc_emails,
                m.subject, m.snippet or m.body_text[:150], m.body_text, m.body_html, m.labels,
                db.jsonb(m.headers), m.internal_date,
            ),
        )
    return {"received": len(batch.messages), "inserted": inserted, "duplicates": len(batch.messages) - inserted}


class CalendarEventIn(BaseModel):
    provider_event_id: str
    title: str = ""
    description: str = ""
    starts_at: datetime
    ends_at: datetime | None = None
    organizer_email: str = ""
    attendees: list[dict] = Field(default_factory=list)
    location: str = ""


class CalendarBatchIn(BaseModel):
    account_email: str
    events: list[CalendarEventIn]


@router.post("/calendar")
def ingest_calendar(batch: CalendarBatchIn, user_id: str = Depends(default_user_id)):
    account = db.q1(
        "SELECT id FROM email_accounts WHERE user_id = %s AND lower(email_address) = lower(%s)",
        (user_id, batch.account_email),
    )
    if not account:
        raise HTTPException(status_code=404, detail=f"no connected account {batch.account_email}")
    inserted = 0
    for ev in batch.events:
        inserted += db.execute(
            """INSERT INTO calendar_events
               (user_id, account_id, provider_event_id, title, description, starts_at, ends_at,
                organizer_email, attendees, location)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (account_id, provider_event_id) DO NOTHING""",
            (
                user_id, account["id"], ev.provider_event_id, ev.title, ev.description, ev.starts_at,
                ev.ends_at, ev.organizer_email, db.jsonb(ev.attendees), ev.location,
            ),
        )
    return {"received": len(batch.events), "inserted": inserted, "duplicates": len(batch.events) - inserted}


class LinkedinRecordIn(BaseModel):
    full_name: str
    url: str = ""
    email: str = ""
    company: str = ""
    position: str = ""
    connected_on: date | None = None


class LinkedinBatchIn(BaseModel):
    records: list[LinkedinRecordIn]


@router.post("/linkedin")
def ingest_linkedin(batch: LinkedinBatchIn, user_id: str = Depends(default_user_id)):
    inserted = 0
    for r in batch.records:
        exists = db.q1(
            "SELECT id FROM linkedin_records WHERE user_id = %s AND lower(full_name) = lower(%s) AND lower(email) = lower(%s)",
            (user_id, r.full_name, r.email),
        )
        if exists:
            continue
        db.execute(
            """INSERT INTO linkedin_records (user_id, full_name, url, email, company, position, connected_on)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (user_id, r.full_name, r.url, r.email.lower(), r.company, r.position, r.connected_on),
        )
        inserted += 1
    return {"received": len(batch.records), "inserted": inserted, "duplicates": len(batch.records) - inserted}
