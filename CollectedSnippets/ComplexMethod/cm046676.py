def anthropic_tool_choice_to_openai(tc: Any) -> Any:
    """Translate Anthropic `tool_choice` into OpenAI `tool_choice`.

    Anthropic formats (all dict shapes with a ``type`` discriminator):

    - ``{"type": "auto"}``                       → ``"auto"``
    - ``{"type": "any"}``                        → ``"required"``
    - ``{"type": "none"}``                       → ``"none"``
    - ``{"type": "tool", "name": "get_weather"}``
          → ``{"type": "function", "function": {"name": "get_weather"}}``

    Returns ``None`` for ``None`` or any unrecognized shape (caller may
    then fall back to its own default, typically ``"auto"``).
    """
    if tc is None:
        return None
    if not isinstance(tc, dict):
        return None
    t = tc.get("type")
    if t == "auto":
        return "auto"
    if t == "any":
        return "required"
    if t == "none":
        return "none"
    if t == "tool":
        name = tc.get("name")
        if not name:
            return None
        return {"type": "function", "function": {"name": name}}
    return None