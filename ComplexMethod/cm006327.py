def derive_agent_environment(agent: dict[str, Any]) -> str:
    environments = agent.get("environments", [])
    if not isinstance(environments, list) or not environments:
        return "unknown"

    has_draft = False
    has_live = False
    for env in environments:
        if not isinstance(env, dict):
            continue
        env_name = str(env.get("name", "")).strip().lower()
        if env_name == ConnectionEnvironment.DRAFT.value:
            has_draft = True
            continue
        if env_name:
            has_live = True

    if has_draft and has_live:
        return "both"
    if has_live:
        return "live"
    if has_draft:
        return "draft"
    return "unknown"