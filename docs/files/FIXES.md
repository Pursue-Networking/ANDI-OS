# FIXES

Log of problems faced and how they were fixed, so any person or agent can avoid repeating them. Add a row whenever a problem is resolved and commit it with the change.

| PROBLEM | FIX | MILESTONE | CAUSE / OCCUR |
| ------- | --- | --------- | ------------- |
| NVIDIA gateway returned 504 on brief generation | Turned think mode off and lowered max_tokens for the brief call in graph.py | 0 | Think mode reasons for thousands of tokens and the response exceeds the gateway timeout |
| psycopg pool could not stop worker threads on script exit | run_pipeline closes the pool explicitly before exiting | 0 | ConnectionPool threads outlive short lived scripts |
| Mem0 search rejected top level user_id parameter | memory.py passes filters with user_id to search and get_all | 0 | Hosted Mem0 API requires entity scoping through filters |
| Default ports 5432 and 6379 already taken locally | docker-compose.yml maps Postgres to 5433 and Redis to 6380 | 0 | Another local stack owns the default ports |
