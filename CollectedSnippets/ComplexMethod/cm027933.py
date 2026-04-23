def parse_seller_response(response_text: str) -> dict:
    """Parse seller agent response into structured data."""
    try:
        if "{" in response_text and "}" in response_text:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            json_str = response_text[start:end]
            data = json.loads(json_str)
            return {
                "action": data.get("action", "counter").lower(),
                "counter_amount": data.get("counter_amount"),
                "message": data.get("message", ""),
                "reasoning": data.get("reasoning", ""),
                "firmness": data.get("firmness", 5)
            }
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback parsing
    response_lower = response_text.lower()
    action = "counter"
    if "accept" in response_lower or "deal" in response_lower:
        action = "accept"
    elif "walk" in response_lower or "goodbye" in response_lower:
        action = "walk"
    elif "reject" in response_lower:
        action = "reject"

    import re
    amount_match = re.search(r'\$?([\d,]+)', response_text)
    counter = int(amount_match.group(1).replace(",", "")) if amount_match else None

    return {
        "action": action,
        "counter_amount": counter,
        "message": response_text[:500],
        "reasoning": "Extracted from response",
        "firmness": 5
    }