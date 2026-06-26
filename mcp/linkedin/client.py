import asyncio
import json
import re

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

TARGET_NAME = "Jayesh Shete"


def print_tool_result(result) -> str:
    """Print tool output and return the combined text."""
    parts = []
    for content_item in result.content:
        text = content_item.text if hasattr(content_item, "text") else str(content_item)
        print(text)
        parts.append(text)
    return "\n".join(parts)


def extract_linkedin_usernames(text: str) -> list[str]:
    """Extract LinkedIn profile slugs from search result text or JSON."""
    usernames: list[str] = []
    seen: set[str] = set()

    try:
        data = json.loads(text)
        for ref in data.get("references", {}).get("search_results", []):
            url = ref.get("url", "")
            match = re.search(r"/in/([^/\s\"'?]+)", url)
            if match and match.group(1) not in seen:
                seen.add(match.group(1))
                usernames.append(match.group(1))
    except json.JSONDecodeError:
        pass

    for match in re.finditer(r"(?:linkedin\.com/in/|/in/)([^/\s\"'?]+)", text):
        slug = match.group(1)
        if slug not in seen:
            seen.add(slug)
            usernames.append(slug)

    return usernames


def extract_email(text: str) -> str | None:
    """Extract the first email address from contact info text."""
    match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return match.group(0) if match else None


async def main():
    server_params = StdioServerParameters(
        command="uvx",
        args=["mcp-server-linkedin@latest"],
        env=None,
    )

    print("Connecting to stickerdaniel/linkedin-mcp-server via uvx...")

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            print("Successfully connected!\n")

            print(f"--- Searching for '{TARGET_NAME}' ---")
            try:
                search_result = await session.call_tool(
                    name="search_people",
                    arguments={"keywords": TARGET_NAME},
                )
                search_text = print_tool_result(search_result)
            except Exception as e:
                print(f"Search failed: {e}")
                return

            linkedin_usernames = extract_linkedin_usernames(search_text)
            if not linkedin_usernames:
                print(
                    f"\nCould not find a LinkedIn username for '{TARGET_NAME}' in search results."
                )
                return

            print(f"\nFound {len(linkedin_usernames)} matching profile(s):")
            for username in linkedin_usernames:
                print(f"  - {username}")

            print("\n--- Checking contact info for each profile ---")
            found_any = False
            for username in linkedin_usernames:
                print(f"\nProfile: {username}")
                try:
                    profile_result = await session.call_tool(
                        name="get_person_profile",
                        arguments={
                            "linkedin_username": username,
                            "sections": "contact_info",
                        },
                    )
                    contact_text = print_tool_result(profile_result)
                    email = extract_email(contact_text)
                    if email:
                        found_any = True
                        print(f"Email: {email}")
                    else:
                        print("Email: not available")
                except Exception as e:
                    print(f"Contact info lookup failed: {e}")

            if not found_any:
                print(
                    "\nNo email found for any matching profile. LinkedIn may hide "
                    "emails unless you are a 1st-degree connection or the person "
                    "made contact info visible."
                )


if __name__ == "__main__":
    asyncio.run(main())
