import asyncio
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def print_tool_result(result) -> str:
    """Print tool output and return the combined text."""
    parts = []
    for content_item in result.content:
        text = content_item.text if hasattr(content_item, "text") else str(content_item)
        print(text)
        parts.append(text)
    return "\n".join(parts)


async def main():
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@gongrzhe/server-gmail-autoauth-mcp"],
        env=None,
    )

    print("Connecting to Gmail MCP server via npx...")

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            print("Successfully connected!\n")

            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description or ''}")

            print("\n--- Listing Gmail labels ---")
            try:
                labels_result = await session.call_tool(
                    name="list_email_labels",
                    arguments={},
                )
                print_tool_result(labels_result)
            except Exception as e:
                print(f"Label listing failed: {e}")
                print(
                    "\nIf auth is missing, run from mcp/gmail:\n"
                    "  ./setup_auth.sh"
                )
                return

            print("\n--- Searching recent inbox emails ---")
            try:
                search_result = await session.call_tool(
                    name="search_emails",
                    arguments={"query": "in:inbox", "maxResults": 5},
                )
                search_text = print_tool_result(search_result)

                try:
                    data = json.loads(search_text)
                    messages = data if isinstance(data, list) else data.get("messages", [])
                    if messages:
                        first_id = messages[0].get("id") or messages[0].get("messageId")
                        if first_id:
                            print(f"\n--- Reading first message ({first_id}) ---")
                            read_result = await session.call_tool(
                                name="read_email",
                                arguments={"messageId": first_id},
                            )
                            print_tool_result(read_result)
                except json.JSONDecodeError:
                    pass
            except Exception as e:
                print(f"Search failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
