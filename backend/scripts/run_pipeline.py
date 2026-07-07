"""Run the full pipeline from the CLI.

    python -m backend.scripts.run_pipeline            # with LLM stages
    python -m backend.scripts.run_pipeline --no-llm   # deterministic stages only
"""

import argparse
import json

from backend.app import db
from backend.app.agents.graph import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the ANDI pipeline for the seeded user.")
    parser.add_argument("--no-llm", action="store_true", help="skip llm stages (triage, embeddings, brief, drafts)")
    parser.add_argument("--trigger", default="manual")
    args = parser.parse_args()

    user = db.q1("SELECT id, full_name FROM users ORDER BY created_at LIMIT 1")
    if not user:
        raise SystemExit("no user in the database, start docker compose so seed.sql applies")
    print(f"Running pipeline for {user['full_name']} ({user['id']})")
    try:
        out = run_pipeline(str(user["id"]), trigger=args.trigger, llm=False if args.no_llm else None)
        print(json.dumps(out, indent=2, default=str))
    finally:
        db.close()


if __name__ == "__main__":
    main()
