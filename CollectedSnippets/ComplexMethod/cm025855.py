def valid_supported_color_modes(
    color_modes: Iterable[ColorMode],
) -> set[ColorMode]:
    """Validate the given color modes."""
    color_modes = set(color_modes)
    if (
        not color_modes
        or ColorMode.UNKNOWN in color_modes
        or (ColorMode.BRIGHTNESS in color_modes and len(color_modes) > 1)
        or (ColorMode.ONOFF in color_modes and len(color_modes) > 1)
        or (ColorMode.WHITE in color_modes and not color_supported(color_modes))
    ):
        raise vol.Error(f"Invalid supported_color_modes {sorted(color_modes)}")
    return color_modes