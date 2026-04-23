def _iter_attention_configs(config, seen = None):
    if config is None or (
        not isinstance(config, dict) and not hasattr(config, "__dict__")
    ):
        return
    if seen is None:
        seen = set()
    config_id = id(config)
    if config_id in seen:
        return
    seen.add(config_id)
    yield config

    for field_name, child_config in _config_items(config):
        if not isinstance(field_name, str) or not field_name.endswith("_config"):
            continue
        if isinstance(child_config, dict) or hasattr(child_config, "__dict__"):
            yield from _iter_attention_configs(child_config, seen)