def _apply_prompt_defaults(req):
    prompt_config = req.setdefault("prompt_config", {})
    for key, value in _DEFAULT_PROMPT_CONFIG.items():
        temp = prompt_config.get(key)
        if (key == "system" and not temp) or key not in prompt_config:
            prompt_config[key] = deepcopy(value)

    if req.get("kb_ids") and not prompt_config.get("parameters") and "{knowledge}" in prompt_config.get("system", ""):
        prompt_config["parameters"] = [{"key": "knowledge", "optional": False}]