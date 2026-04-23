async def _setup_automation_or_script(
    hass: HomeAssistant,
    domain: str,
    configs: list[dict[str, Any]],
    script_config: dict[str, Any] | None = None,
    stored_traces: int | None = None,
) -> None:
    """Set up automations or scripts from automation config."""
    if domain == "script":
        configs = {config["id"]: {"sequence": config["actions"]} for config in configs}

    if script_config:
        if domain == "automation":
            assert await async_setup_component(
                hass, "script", {"script": script_config}
            )
        else:
            configs = {**configs, **script_config}

    if stored_traces is not None:
        if domain == "script":
            for config in configs.values():
                config["trace"] = {}
                config["trace"]["stored_traces"] = stored_traces
        else:
            for config in configs:
                config["trace"] = {}
                config["trace"]["stored_traces"] = stored_traces

    assert await async_setup_component(hass, domain, {domain: configs})