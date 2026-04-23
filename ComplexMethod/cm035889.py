def _make_settings(
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    max_iterations: int | None = None,
    agent: str | None = None,
    language: str | None = None,
    **extra_agent: object,
) -> DataSettings:
    """Build a DataSettings with diff-only nested settings payloads."""
    top_level: dict = {}
    if language is not None:
        top_level['language'] = language
    s = DataSettings(**top_level)
    llm: dict = {}
    if model is not None:
        llm['model'] = model
    if base_url is not None:
        llm['base_url'] = base_url
    if api_key is not None:
        llm['api_key'] = api_key
    agent_settings_diff: dict = {}
    if agent is not None:
        agent_settings_diff['agent'] = agent
    if llm:
        agent_settings_diff['llm'] = llm
    agent_settings_diff.update(extra_agent)
    payload: dict = {}
    if agent_settings_diff:
        payload['agent_settings_diff'] = agent_settings_diff
    conversation_settings_diff: dict = {}
    if max_iterations is not None:
        conversation_settings_diff['max_iterations'] = max_iterations
    if conversation_settings_diff:
        payload['conversation_settings_diff'] = conversation_settings_diff
    if payload:
        s.update(payload)
    return s