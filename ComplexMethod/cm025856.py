def filter_turn_on_params(light: LightEntity, params: dict[str, Any]) -> dict[str, Any]:
    """Filter out params not supported by the light."""
    supported_features = light.supported_features

    if LightEntityFeature.EFFECT not in supported_features:
        params.pop(ATTR_EFFECT, None)
    if LightEntityFeature.FLASH not in supported_features:
        params.pop(ATTR_FLASH, None)
    if LightEntityFeature.TRANSITION not in supported_features:
        params.pop(ATTR_TRANSITION, None)

    supported_color_modes = (
        light._light_internal_supported_color_modes  # noqa: SLF001
    )
    if not brightness_supported(supported_color_modes):
        params.pop(ATTR_BRIGHTNESS, None)
    if ColorMode.COLOR_TEMP not in supported_color_modes:
        params.pop(ATTR_COLOR_TEMP_KELVIN, None)
    if ColorMode.HS not in supported_color_modes:
        params.pop(ATTR_HS_COLOR, None)
    if ColorMode.RGB not in supported_color_modes:
        params.pop(ATTR_RGB_COLOR, None)
    if ColorMode.RGBW not in supported_color_modes:
        params.pop(ATTR_RGBW_COLOR, None)
    if ColorMode.RGBWW not in supported_color_modes:
        params.pop(ATTR_RGBWW_COLOR, None)
    if ColorMode.WHITE not in supported_color_modes:
        params.pop(ATTR_WHITE, None)
    if ColorMode.XY not in supported_color_modes:
        params.pop(ATTR_XY_COLOR, None)

    return params