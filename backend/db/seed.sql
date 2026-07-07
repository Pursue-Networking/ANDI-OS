-- =============================================================================
-- ANDI DUMMY SEED DATA v0
-- Only the RAW layer is seeded. Contacts, observations, interactions, scores,
-- signals, briefs and drafts are all produced by the pipeline, so running the
-- pipeline on a fresh database shows the entire flow end to end.
--
-- The data is written so every noise class and every signal type fires:
--   real humans:   Kolin (unanswered question), Soham (healthy thread),
--                  Dr. Anita Rao (gone quiet), Daud (meeting, no follow up),
--                  Marcus (unanswered recruiter), Priya (fresh warm intro),
--                  Alex (user wrote, no answer)
--   clear noise:   newsletter, github, linkedin jobs, stripe receipt,
--                  mailchimp blast, calendar bot, support auto-ack, promo spam
--   uncertain:     human-written cold sales, community digest with a personal
--                  mention, semi-templated event invite
-- Timestamps are relative to now() so signals always fire on a fresh seed.
-- =============================================================================

INSERT INTO users (id, email, full_name) VALUES
('11111111-1111-1111-1111-111111111111', 'bhuvnesh@andi.local', 'Bhuvnesh Verma');

INSERT INTO email_accounts (id, user_id, provider, email_address, display_name) VALUES
('22222222-2222-2222-2222-222222222222', '11111111-1111-1111-1111-111111111111', 'gmail', 'bhuvnesh@andi.local', 'Bhuvnesh Verma');

-- ---------------------------------------------------------------------------
-- RAW EMAILS
-- ---------------------------------------------------------------------------

INSERT INTO raw_emails
(id, user_id, account_id, gmail_message_id, gmail_thread_id, direction, from_email, from_name, to_emails, cc_emails, subject, snippet, body_text, labels, headers, internal_date) VALUES

-- THREAD 1: Kolin. Real client. His last question is still unanswered -> no_reply_inbound.
('ee000000-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
 'gm-0001', 'th-0001', 'outbound', 'bhuvnesh@andi.local', 'Bhuvnesh Verma', '{kolin@roswellventures.com}', '{}',
 'Revised scope for ANDI phase 1', 'Kolin, here is the revised phase 1 scope we discussed...',
 'Hi Kolin, here is the revised phase 1 scope we discussed on the call. Ingestion first, scoring second. Let me know if the split looks right. Best, Bhuvnesh',
 '{SENT}', '{}', now() - interval '9 days 3 hours'),

('ee000000-0000-0000-0000-000000000002', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
 'gm-0002', 'th-0001', 'inbound', 'kolin@roswellventures.com', 'Kolin Roswell', '{bhuvnesh@andi.local}', '{}',
 'Re: Revised scope for ANDI phase 1', 'Thanks Bhuvnesh, reviewing this with Soham today...',
 'Thanks Bhuvnesh, reviewing this with Soham today. The direction looks right to me. Kolin',
 '{INBOX}', '{}', now() - interval '8 days 5 hours'),

('ee000000-0000-0000-0000-000000000003', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
 'gm-0003', 'th-0001', 'inbound', 'kolin@roswellventures.com', 'Kolin Roswell', '{bhuvnesh@andi.local}', '{}',
 'Re: Revised scope for ANDI phase 1', 'One more thing, can you send the milestone budget split...',
 'Hi Bhuvnesh, one more thing. Can you send the revised milestone budget split? I need it before the board sync on Friday. Kolin',
 '{INBOX,IMPORTANT}', '{}', now() - interval '6 days 2 hours'),

-- THREAD 2: Soham intro to Priya. Healthy thread, user replied fast.
('ee000000-0000-0000-0000-000000000004', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
 'gm-0004', 'th-0002', 'inbound', 'soham@pursuenetworking.com', 'Soham Shah', '{bhuvnesh@andi.local}', '{priya@meridian.vc}',
 'Intro: Priya Mehta (Meridian VC)', 'Bhuvnesh meet Priya, she leads early stage at Meridian...',
 'Hi Bhuvnesh, meet Priya Mehta. She leads early stage investments at Meridian and asked about relationship intelligence tools. Priya, Bhuvnesh is building ANDI. I will let you two take it from here. Soham',
 '{INBOX,IMPORTANT}', '{}', now() - interval '2 days 4 hours'),

('ee000000-0000-0000-0000-000000000005', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
 'gm-0005', 'th-0002', 'outbound', 'bhuvnesh@andi.local', 'Bhuvnesh Verma', '{priya@meridian.vc}', '{soham@pursuenetworking.com}',
 'Re: Intro: Priya Mehta (Meridian VC)', 'Thanks Soham. Priya, great to meet you...',
 'Thanks Soham. Priya, great to meet you. Happy to walk you through what we are building. Does a short call next week work? Bhuvnesh',
 '{SENT}', '{}', now() - interval '1 day 6 hours'),

-- THREAD 3: Dr. Anita Rao. Real mentor, last touch 74 days ago -> gone_quiet.
('ee000000-0000-0000-0000-000000000006', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
 'gm-0006', 'th-0003', 'inbound', 'anita.rao@univmail.edu', 'Dr. Anita Rao', '{bhuvnesh@andi.local}', '{}',
 'Great catching up at the alumni meet', 'Bhuvnesh, it was lovely hearing about your startup...',
 'Bhuvnesh, it was lovely hearing about your startup at the alumni meet. Keep me posted on the progress. Dr. Rao',
 '{INBOX}', '{}', now() - interval '75 days'),

('ee000000-0000-0000-0000-000000000007', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
 'gm-0007', 'th-0003', 'outbound', 'bhuvnesh@andi.local', 'Bhuvnesh Verma', '{anita.rao@univmail.edu}', '{}',
 'Re: Great catching up at the alumni meet', 'Thank you, will do...',
 'Thank you Dr. Rao, will keep you posted. It meant a lot. Bhuvnesh',
 '{SENT}', '{}', now() - interval '74 days'),

-- THREAD 4: Daud. Meeting happened 10 days ago, no email after -> no_followup_meeting.
('ee000000-0000-0000-0000-000000000008', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
 'gm-0008', 'th-0004', 'inbound', 'daud@buildscale.dev', 'Daud Khan', '{bhuvnesh@andi.local}', '{}',
 'Agenda for our architecture review', 'Sending over the points I want to cover on Thursday...',
 'Hi Bhuvnesh, sending over the points I want to cover on Thursday: queue design, token storage, and the sync cursor. Daud',
 '{INBOX}', '{}', now() - interval '12 days'),

('ee000000-0000-0000-0000-000000000009', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
 'gm-0009', 'th-0004', 'outbound', 'bhuvnesh@andi.local', 'Bhuvnesh Verma', '{daud@buildscale.dev}', '{}',
 'Re: Agenda for our architecture review', 'Sounds good, see you Thursday...',
 'Sounds good Daud, see you Thursday. Bhuvnesh',
 '{SENT}', '{}', now() - interval '11 days'),

-- THREAD 5: Marcus. Real recruiter, personalized, unanswered 4 days -> no_reply_inbound.
('ee000000-0000-0000-0000-000000000010', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
 'gm-0010', 'th-0005', 'inbound', 'marcus.lee@talentbridge.io', 'Marcus Lee', '{bhuvnesh@andi.local}', '{}',
 'Founding engineer role at a memory startup', 'Bhuvnesh, loved your ANDI writeup on relationship graphs...',
 'Hi Bhuvnesh, loved your ANDI writeup on relationship graphs. A portfolio company is hiring a founding engineer and your profile fits. Open to a chat this week? Marcus',
 '{INBOX}', '{}', now() - interval '4 days'),

-- THREAD 6: Priya writes directly after the intro -> new_intro, fresh and warm.
('ee000000-0000-0000-0000-000000000011', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
 'gm-0011', 'th-0006', 'inbound', 'priya@meridian.vc', 'Priya Mehta', '{bhuvnesh@andi.local}', '{}',
 'Great to connect', 'Following up on Soham intro, does Tuesday work for coffee...',
 'Hi Bhuvnesh, following up on the intro from Soham. Does Tuesday afternoon work for a coffee near Indiranagar? Priya',
 '{INBOX,IMPORTANT}', '{}', now() - interval '1 day'),

-- THREAD 7: user wrote to Alex, no answer for 20 days -> waiting_on_them.
('ee000000-0000-0000-0000-000000000012', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
 'gm-0012', 'th-0007', 'outbound', 'bhuvnesh@andi.local', 'Bhuvnesh Verma', '{alex@founderclub.org}', '{}',
 'Demo of ANDI at your founder circle', 'Would love to show ANDI to the founder circle...',
 'Hi Alex, would love to show ANDI to the founder circle next month. Fifteen minutes, live data, no slides. Interested? Bhuvnesh',
 '{SENT}', '{}', now() - interval '20 days'),

-- NOISE: weekly newsletter, bulk headers, two issues.
('ee000000-0000-0000-0000-000000000013', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
 'gm-0013', 'th-0008', 'inbound', 'digest@mail.startupdigest.com', 'The Startup Digest', '{bhuvnesh@andi.local}', '{}',
 'Your weekly startup digest #214', 'This week: 12 funding rounds, 3 acquisitions...',
 'This week in startups: 12 funding rounds, 3 acquisitions, and the tools everyone is talking about. Read online. Unsubscribe at any time.',
 '{INBOX,CATEGORY_UPDATES}', '{"List-Unsubscribe": "<mailto:unsub@mail.startupdigest.com>", "Precedence": "bulk"}', now() - interval '3 days'),

('ee000000-0000-0000-0000-000000000014', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
 'gm-0014', 'th-0009', 'inbound', 'digest@mail.startupdigest.com', 'The Startup Digest', '{bhuvnesh@andi.local}', '{}',
 'Your weekly startup digest #213', 'This week: the rise of memory layers...',
 'This week in startups: the rise of memory layers, 9 funding rounds, and more. Read online. Unsubscribe at any time.',
 '{INBOX,CATEGORY_UPDATES}', '{"List-Unsubscribe": "<mailto:unsub@mail.startupdigest.com>", "Precedence": "bulk"}', now() - interval '10 days'),

-- NOISE: github notification, auto-generated.
('ee000000-0000-0000-0000-000000000015', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
 'gm-0015', 'th-0010', 'inbound', 'notifications@github.com', 'GitHub', '{bhuvnesh@andi.local}', '{}',
 '[MasterBhuvnesh/ANDI-OS] Run failed: CI on dev', 'Run failed for dev...',
 'Run failed for dev. Job: build. Step: pytest. View the run on GitHub.',
 '{INBOX,CATEGORY_UPDATES}', '{"Auto-Submitted": "auto-generated", "Precedence": "list"}', now() - interval '2 days'),

-- NOISE: linkedin job alerts.
('ee000000-0000-0000-0000-000000000016', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
 'gm-0016', 'th-0011', 'inbound', 'no-reply@linkedin.com', 'LinkedIn', '{bhuvnesh@andi.local}', '{}',
 '5 new jobs for founding engineer', 'Jobs you may be interested in...',
 'Here are 5 new jobs that match founding engineer in Bangalore. See all jobs. Unsubscribe.',
 '{INBOX,CATEGORY_UPDATES}', '{"List-Unsubscribe": "<https://www.linkedin.com/unsub>", "Auto-Submitted": "auto-generated"}', now() - interval '5 days'),

-- NOISE: stripe receipt, transactional.
('ee000000-0000-0000-0000-000000000017', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
 'gm-0017', 'th-0012', 'inbound', 'receipts@stripe.com', 'Stripe', '{bhuvnesh@andi.local}', '{}',
 'Your receipt from Pursue Networking #1042', 'Receipt for your payment of $49.00...',
 'Receipt #1042. Amount paid: $49.00. Thanks for your payment to Pursue Networking.',
 '{INBOX,CATEGORY_UPDATES}', '{"Auto-Submitted": "auto-generated"}', now() - interval '7 days'),

-- NOISE: marketing blast with spam wording.
('ee000000-0000-0000-0000-000000000018', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
 'gm-0018', 'th-0013', 'inbound', 'hello@growthhackpro.io', 'GrowthHack Pro', '{bhuvnesh@andi.local}', '{}',
 '10x your pipeline with AI SDRs (last chance)', 'Limited time offer, book a demo today...',
 'Hi there, stop leaving revenue on the table. 10x your pipeline with our AI SDR platform. Limited time offer, book a demo today. Click here to unsubscribe.',
 '{INBOX,CATEGORY_PROMOTIONS}', '{"List-Unsubscribe": "<https://growthhackpro.io/unsub>", "X-Mailer": "Mailchimp"}', now() - interval '3 days 6 hours'),

-- NOISE: calendar bot reminder.
('ee000000-0000-0000-0000-000000000019', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
 'gm-0019', 'th-0014', 'inbound', 'calendar-notification@google.com', 'Google Calendar', '{bhuvnesh@andi.local}', '{}',
 'Reminder: Intro call with Priya Mehta', 'Tomorrow at 3pm...',
 'This is a reminder for Intro call with Priya Mehta tomorrow at 3pm.',
 '{INBOX,CATEGORY_UPDATES}', '{"Auto-Submitted": "auto-generated"}', now() - interval '1 day 2 hours'),

-- NOISE: support auto-ack.
('ee000000-0000-0000-0000-000000000020', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
 'gm-0020', 'th-0015', 'inbound', 'support@saastool.com', 'SaasTool Support', '{bhuvnesh@andi.local}', '{}',
 'We received your ticket #8841', 'Your request has been received...',
 'Your request has been received and a support agent will reply shortly. Ticket #8841. Do not reply to this email.',
 '{INBOX,CATEGORY_UPDATES}', '{"Auto-Submitted": "auto-replied"}', now() - interval '6 days'),

-- NOISE: promo spam.
('ee000000-0000-0000-0000-000000000021', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
 'gm-0021', 'th-0016', 'inbound', 'promo@flightdeals.example', 'FlightDeals', '{bhuvnesh@andi.local}', '{}',
 '50% OFF international flights this week only', 'Do not miss these exclusive deals...',
 'Do not miss these exclusive deals. 50% off international flights, this week only. Book now. Unsubscribe.',
 '{INBOX,CATEGORY_PROMOTIONS}', '{"List-Unsubscribe": "<mailto:stop@flightdeals.example>", "Precedence": "bulk"}', now() - interval '2 days 8 hours'),

-- UNCERTAIN: human-written cold sales, personalized, clean headers. LLM must judge.
('ee000000-0000-0000-0000-000000000022', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
 'gm-0022', 'th-0017', 'inbound', 'jordan@pipelineiq.io', 'Jordan Blake', '{bhuvnesh@andi.local}', '{}',
 'Your take on relationship-first outreach', 'Read your post about ANDI and citation gates...',
 'Hi Bhuvnesh, read your post about ANDI and the citation gate idea. We hit the same wall at PipelineIQ. I run partnerships there. If you are open to comparing notes I would enjoy a short call. Jordan',
 '{INBOX}', '{}', now() - interval '3 days 2 hours'),

-- UNCERTAIN: community digest that mentions the user personally, but bulk headers.
('ee000000-0000-0000-0000-000000000023', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
 'gm-0023', 'th-0018', 'inbound', 'community@indiehackers.example', 'Indie Hackers', '{bhuvnesh@andi.local}', '{}',
 'Your post hit the front page + this week digest', 'Congrats, your ANDI post is trending...',
 'Congrats Bhuvnesh, your ANDI post hit the front page this week. Also in this digest: 8 launches and a pricing teardown. Unsubscribe.',
 '{INBOX,CATEGORY_UPDATES}', '{"List-Unsubscribe": "<https://indiehackers.example/unsub>", "Precedence": "bulk"}', now() - interval '4 days'),

-- UNCERTAIN: semi-templated event invite, clean headers.
('ee000000-0000-0000-0000-000000000024', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
 'gm-0024', 'th-0019', 'inbound', 'events@blrfounders.in', 'BLR Founders', '{bhuvnesh@andi.local}', '{}',
 'You are invited: Bangalore founders dinner', '12 seats, next Thursday...',
 'Hi Bhuvnesh, you are invited to the Bangalore founders dinner next Thursday. 12 seats, invite only. Reply to confirm.',
 '{INBOX}', '{}', now() - interval '5 days 4 hours');

-- ---------------------------------------------------------------------------
-- CALENDAR EVENTS
-- ---------------------------------------------------------------------------

INSERT INTO calendar_events
(id, user_id, account_id, provider_event_id, title, description, starts_at, ends_at, organizer_email, attendees, location) VALUES

-- Past meeting with Daud, no email after it -> no_followup_meeting.
('ca000000-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
 'ev-0001', 'Architecture review with Daud', 'Queue design, token storage, sync cursor',
 now() - interval '10 days', now() - interval '10 days' + interval '1 hour',
 'bhuvnesh@andi.local', '[{"email": "daud@buildscale.dev", "name": "Daud Khan", "response": "accepted"}]', 'Meet'),

-- Upcoming call with Priya.
('ca000000-0000-0000-0000-000000000002', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
 'ev-0002', 'Intro call with Priya Mehta', 'Walkthrough of ANDI',
 now() + interval '1 day', now() + interval '1 day' + interval '30 minutes',
 'bhuvnesh@andi.local', '[{"email": "priya@meridian.vc", "name": "Priya Mehta", "response": "accepted"}]', 'Meet'),

-- Old mentor sync with Dr. Rao, does not break the gone_quiet window.
('ca000000-0000-0000-0000-000000000003', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
 'ev-0003', 'Quarterly mentor sync', 'Catch up with Dr. Rao',
 now() - interval '100 days', now() - interval '100 days' + interval '45 minutes',
 'anita.rao@univmail.edu', '[{"email": "anita.rao@univmail.edu", "name": "Dr. Anita Rao", "response": "accepted"}]', 'Campus');

-- ---------------------------------------------------------------------------
-- LINKEDIN EXPORT
-- ---------------------------------------------------------------------------

INSERT INTO linkedin_records (id, user_id, full_name, url, email, company, position, connected_on) VALUES
('fe000000-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111', 'Kolin Roswell', 'https://linkedin.com/in/kolinroswell', 'kolin@roswellventures.com', 'Roswell Ventures', 'Managing Partner', now()::date - 400),
('fe000000-0000-0000-0000-000000000002', '11111111-1111-1111-1111-111111111111', 'Soham Shah', 'https://linkedin.com/in/sohamshah', 'soham@pursuenetworking.com', 'Pursue Networking', 'CEO', now()::date - 300),
('fe000000-0000-0000-0000-000000000003', '11111111-1111-1111-1111-111111111111', 'Daud Khan', 'https://linkedin.com/in/daudkhan', 'daud@buildscale.dev', 'BuildScale', 'Founding Engineer', now()::date - 250),
('fe000000-0000-0000-0000-000000000004', '11111111-1111-1111-1111-111111111111', 'Priya Mehta', 'https://linkedin.com/in/priyamehta', 'priya@meridian.vc', 'Meridian VC', 'Principal', now()::date - 2),
('fe000000-0000-0000-0000-000000000005', '11111111-1111-1111-1111-111111111111', 'Dr. Anita Rao', 'https://linkedin.com/in/anitarao', 'anita.rao@univmail.edu', 'University', 'Professor', now()::date - 700);
