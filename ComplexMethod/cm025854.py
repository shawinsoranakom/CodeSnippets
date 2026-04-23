def filter_supported_color_modes(color_modes: Iterable[ColorMode]) -> set[ColorMode]:
    """Filter the given color modes."""
    color_modes = set(color_modes)
    if (
        not color_modes
        or ColorMode.UNKNOWN in color_modes
        or (ColorMode.WHITE in color_modes and not color_supported(color_modes))
    ):
        raise HomeAssistantError

    if ColorMode.ONOFF in color_modes and len(color_modes) > 1:
        color_modes.remove(ColorMode.ONOFF)
    if ColorMode.BRIGHTNESS in color_modes and len(color_modes) > 1:
        color_modes.remove(ColorMode.BRIGHTNESS)
    return color_modes