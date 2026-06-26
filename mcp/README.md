# MCP

This folder holds ANDI's Model Context Protocol (MCP) servers: the private integration layer that exposes Gmail, Calendar, and LinkedIn-derived data sources to the ANDI application as callable tools.

Each data source lives in its own subfolder, for example:

| Folder      | Purpose                                                      |
| ----------- | ----------------------------------------------------------- |
| `linkedin/` | LinkedIn-derived relationship data ingestion and import     |
| `gmail/`    | Gmail thread/message ingestion and draft tool-calling       |
| `calendar/` | Calendar event ingestion and attendee extraction            |

## Conventions

* One MCP server per data source, in its own subfolder with its own README.
* Credentials and keys stay **outside** the codebase (environment variables or a credentials manager) — never committed.
* No outreach is sent automatically; draft tools create and update drafts only.