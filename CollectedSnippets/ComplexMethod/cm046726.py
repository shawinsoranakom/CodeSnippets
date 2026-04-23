def llm_classify_columns(
    column_names: list[str],
    samples: list[dict],
) -> Optional[dict[str, str]]:
    """
    Ask a helper LLM to classify dataset columns into roles.

    Called when heuristic column detection fails (returns None).

    Args:
        column_names: Column names in the dataset.
        samples: 3-5 sample rows with values truncated to 200 chars.

    Returns:
        Dict mapping column_name → role ("user"|"assistant"|"system"|"metadata"),
        or None on failure.
    """
    formatted = ""
    for i, row in enumerate(samples[:5], 1):
        parts = []
        for col in column_names:
            val = str(row.get(col, ""))[:200]
            parts.append(f"  {col}: {val}")
        formatted += f"Sample {i}:\n" + "\n".join(parts) + "\n\n"

    prompt = (
        "Classify each column in this dataset into one of these roles:\n"
        "- user: The input/question/prompt from the human\n"
        "- assistant: The expected output/answer/response from the AI\n"
        "- system: Context, persona, or task description\n"
        "- metadata: IDs, scores, labels, timestamps — not part of conversation\n\n"
        f"Columns: {column_names}\n\n"
        f"{formatted}"
        "Respond with ONLY a JSON object mapping column names to roles.\n"
        'Example: {"question": "user", "answer": "assistant", "id": "metadata"}'
    )

    result = _run_with_helper(prompt, max_tokens = 200)
    if not result:
        return None

    # Parse JSON from response (may have markdown fences)
    text = result.strip()
    if text.startswith("```"):
        # Strip markdown code fence
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        text = text.strip()

    try:
        mapping = json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in the response
        import re

        match = re.search(r"\{[^}]+\}", text)
        if match:
            try:
                mapping = json.loads(match.group())
            except json.JSONDecodeError:
                logger.warning(f"Could not parse helper model JSON: {text!r}")
                return None
        else:
            logger.warning(f"No JSON found in helper model response: {text!r}")
            return None

    if not isinstance(mapping, dict):
        return None

    # Validate: all values must be valid roles
    valid_roles = {"user", "assistant", "system", "metadata"}
    cleaned = {}
    for col, role in mapping.items():
        if (
            col in column_names
            and isinstance(role, str)
            and role.lower() in valid_roles
        ):
            cleaned[col] = role.lower()

    if not cleaned:
        return None

    # Must have at least user + assistant
    roles_present = set(cleaned.values())
    if "user" not in roles_present or "assistant" not in roles_present:
        logger.warning(f"Helper model mapping missing user/assistant: {cleaned}")
        return None

    logger.info(f"LLM-classified columns: {cleaned}")
    return cleaned