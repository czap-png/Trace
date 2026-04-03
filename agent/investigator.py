import json
import anthropic
from dotenv import load_dotenv
from agent.tools import TOOL_DEFINITIONS, TOOL_FUNCTIONS

load_dotenv()

client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are an expert investigative analyst working for Trace, an entity investigation tool.

Your job is to investigate companies and individuals using the tools available to you.

When given a name to investigate:
1. Search for the entity in the database
2. Look up their relationships and connections
3. Check for risk flags and sanctions
4. Search documents for additional context
5. Follow interesting leads — if you find connected entities, investigate those too
6. Write a clear, structured investigation report

Your report should include:
- Who the entity is and basic details
- Key relationships and connections
- Any risk flags or sanctions
- Notable findings from documents
- A risk assessment (High / Medium / Low / Clean)
- Recommended follow-up leads

Always cite which data source each finding comes from.
Be direct and factual. Flag when something is unverified."""


def run_investigation(query: str) -> str:
    print(f"\n Searching: {query}\n")

    messages = [
        {"role": "user", "content": f"Please investigate: {query}"}
    ]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=messages
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            final_text = next(
                (block.text for block in response.content if hasattr(block, "text")),
                "No report generated."
            )
            return final_text

        tool_uses = [block for block in response.content if block.type == "tool_use"]

        if not tool_uses:
            break

        tool_results = []
        for tool_use in tool_uses:
            tool_name = tool_use.name
            tool_input = tool_use.input

            print(f"  Calling: {tool_name}({json.dumps(tool_input)})")

            tool_fn = TOOL_FUNCTIONS.get(tool_name)
            if tool_fn:
                result = tool_fn(**tool_input)
            else:
                result = {"error": f"Unknown tool: {tool_name}"}

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": json.dumps(result)
            })

        messages.append({"role": "user", "content": tool_results})

    return "Investigation complete."


if __name__ == "__main__":
    report = run_investigation("Ajay Gupta")
    print("\n" + "="*60)
    print("INVESTIGATION REPORT")
    print("="*60)
    print(report)