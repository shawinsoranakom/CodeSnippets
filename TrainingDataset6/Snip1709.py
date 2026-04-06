def _html_safe_json(value: Any) -> str:
    """Serialize a value to JSON with HTML special characters escaped.

    This prevents injection when the JSON is embedded inside a <script> tag.
    """
    return (
        json.dumps(value)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )