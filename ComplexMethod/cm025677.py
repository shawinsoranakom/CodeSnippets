def async_get_homekit_discovery(
    homekit_model_lookups: dict[str, HomeKitDiscoveredIntegration],
    homekit_model_matchers: dict[re.Pattern, HomeKitDiscoveredIntegration],
    props: dict[str, Any],
) -> HomeKitDiscoveredIntegration | None:
    """Handle a HomeKit discovery.

    Return the domain to forward the discovery data to
    """
    if not (
        model := props.get(HOMEKIT_MODEL_LOWER) or props.get(HOMEKIT_MODEL_UPPER)
    ) or not isinstance(model, str):
        return None

    for split_str in _HOMEKIT_MODEL_SPLITS:
        key = (model.split(split_str))[0] if split_str else model
        if discovery := homekit_model_lookups.get(key):
            return discovery

    for pattern, discovery in homekit_model_matchers.items():
        if pattern.match(model):
            return discovery

    return None