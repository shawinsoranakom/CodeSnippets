def _parse_json_response(text: str) -> Optional[dict]:
    """Parse JSON from LLM response, handling markdown fences and noise."""
    if not text:
        return None

    cleaned = text.strip()

    # Strip markdown code fences
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        end = -1 if lines[-1].strip().startswith("```") else len(lines)
        cleaned = "\n".join(lines[1:end]).strip()

    # Try direct parse
    try:
        obj = json.loads(cleaned)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    # Greedy match for outermost {...}
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            obj = json.loads(match.group())
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass

    return None