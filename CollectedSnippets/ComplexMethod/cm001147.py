async def _summarize_messages_llm(
    messages: list[dict],
    client: AsyncOpenAI,
    model: str,
    timeout: float = 30.0,
) -> str:
    """Summarize messages using an LLM."""
    conversation = []
    for msg in messages:
        # Responses API: function_call items
        if msg.get("type") == "function_call":
            name = msg.get("name", "unknown_tool")
            args = msg.get("arguments", "")
            conversation.append(f"TOOL CALL ({name}): {args}")
            continue
        # Responses API: function_call_output items
        if msg.get("type") == "function_call_output":
            output = msg.get("output", "")
            conversation.append(f"TOOL OUTPUT: {output}")
            continue

        role = msg.get("role", "")
        content = msg.get("content", "")
        if content and role in ("user", "assistant", "tool"):
            conversation.append(f"{role.upper()}: {content}")

    conversation_text = "\n\n".join(conversation)

    if not conversation_text:
        return "No conversation history available."

    # Limit to ~100k chars for safety
    MAX_CHARS = 100_000
    if len(conversation_text) > MAX_CHARS:
        conversation_text = conversation_text[:MAX_CHARS] + "\n\n[truncated]"

    response = await client.with_options(timeout=timeout).chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Create a factual summary of the conversation so far. "
                    "This summary will be used as context when continuing the conversation.\n\n"
                    "CRITICAL: Only include information that is EXPLICITLY present in the "
                    "conversation. Do NOT fabricate, infer, or invent any details. "
                    "If a section has no relevant content in the conversation, skip it entirely.\n\n"
                    "Before writing the summary, analyze each message chronologically to identify:\n"
                    "- User requests and their explicit goals\n"
                    "- Actions taken and key decisions made\n"
                    "- Technical specifics (file names, tool outputs, function signatures)\n"
                    "- Errors encountered and resolutions applied\n\n"
                    "IMPORTANT: Preserve all concrete references verbatim — these are small but "
                    "critical for continuing the conversation:\n"
                    "- File paths and directory paths (e.g. /src/app/page.tsx, ./output/result.csv)\n"
                    "- Image/media file paths from tool outputs\n"
                    "- URLs, API endpoints, and webhook addresses\n"
                    "- Resource IDs, session IDs, and identifiers\n"
                    "- Tool names that were called and their key parameters\n"
                    "- Environment variables, config keys, and credentials names (not values)\n\n"
                    "Include ONLY the sections below that have relevant content "
                    "(skip sections with nothing to report):\n\n"
                    "## 1. Primary Request and Intent\n"
                    "The user's explicit goals and what they are trying to accomplish.\n\n"
                    "## 2. Key Technical Concepts\n"
                    "Technologies, frameworks, tools, and patterns being used or discussed.\n\n"
                    "## 3. Files and Resources Involved\n"
                    "Specific files examined or modified, with relevant snippets and identifiers. "
                    "Include exact file paths, image paths from tool outputs, and resource URLs.\n\n"
                    "## 4. Errors and Fixes\n"
                    "Problems encountered, error messages, and their resolutions.\n\n"
                    "## 5. All User Messages\n"
                    "A complete list of all user inputs (excluding tool outputs) "
                    "to preserve their exact requests.\n\n"
                    "## 6. Pending Tasks\n"
                    "Work items the user explicitly requested that have not yet been completed.\n\n"
                    "## 7. Current State\n"
                    "What was happening most recently in the conversation."
                ),
            },
            {"role": "user", "content": f"Summarize:\n\n{conversation_text}"},
        ],
        max_tokens=2000,
        temperature=0.3,
    )

    return response.choices[0].message.content or "No summary available."