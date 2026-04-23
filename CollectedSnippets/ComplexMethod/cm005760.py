def _process_template_field(
    field: dict[str, Any],
    *,
    strip_secrets: bool,
    code_as_lines: bool,
) -> dict[str, Any]:
    """Return a (possibly mutated copy of) a single template field dict."""
    field = dict(field)

    if strip_secrets and (field.get("password") or field.get("load_from_db")):
        field["value"] = ""

    if code_as_lines and field.get("type") == "code":
        value = field.get("value")
        if isinstance(value, str):
            field["value"] = value.split("\n")
        elif isinstance(value, list):
            pass  # already lines -- leave as-is

    return field