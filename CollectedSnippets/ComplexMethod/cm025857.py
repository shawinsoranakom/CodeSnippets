def process_turn_on_params(  # noqa: C901
    hass: HomeAssistant, light: LightEntity, params: dict[str, Any]
) -> dict[str, Any]:
    """Process light turn on params."""
    params = dict(params)

    # Only process params once we processed brightness step
    if params and (
        ATTR_BRIGHTNESS_STEP in params or ATTR_BRIGHTNESS_STEP_PCT in params
    ):
        brightness = light.brightness if light.is_on and light.brightness else 0

        if ATTR_BRIGHTNESS_STEP in params:
            brightness += params.pop(ATTR_BRIGHTNESS_STEP)

        else:
            brightness_pct = round(brightness / 255 * 100)
            brightness = round(
                (brightness_pct + params.pop(ATTR_BRIGHTNESS_STEP_PCT)) / 100 * 255
            )

        params[ATTR_BRIGHTNESS] = max(0, min(255, brightness))

        preprocess_turn_on_alternatives(hass, params)

    if (not params or not light.is_on) or (params and ATTR_TRANSITION not in params):
        hass.data[DATA_PROFILES].apply_default(light.entity_id, light.is_on, params)

    supported_color_modes = light._light_internal_supported_color_modes  # noqa: SLF001

    # If a color temperature is specified, emulate it if not supported by the light
    if ATTR_COLOR_TEMP_KELVIN in params:
        if (
            ColorMode.COLOR_TEMP not in supported_color_modes
            and ColorMode.RGBWW in supported_color_modes
        ):
            color_temp = params.pop(ATTR_COLOR_TEMP_KELVIN)
            brightness = cast(int, params.get(ATTR_BRIGHTNESS, light.brightness))
            params[ATTR_RGBWW_COLOR] = color_util.color_temperature_to_rgbww(
                color_temp,
                brightness,
                light.min_color_temp_kelvin,
                light.max_color_temp_kelvin,
            )
        elif ColorMode.COLOR_TEMP not in supported_color_modes:
            color_temp = params.pop(ATTR_COLOR_TEMP_KELVIN)
            if color_supported(supported_color_modes):
                params[ATTR_HS_COLOR] = color_util.color_temperature_to_hs(color_temp)

    # If a color is specified, convert to the color space supported by the light
    rgb_color: tuple[int, int, int] | None
    rgbww_color: tuple[int, int, int, int, int] | None
    if ATTR_HS_COLOR in params and ColorMode.HS not in supported_color_modes:
        hs_color = params.pop(ATTR_HS_COLOR)
        if ColorMode.RGB in supported_color_modes:
            params[ATTR_RGB_COLOR] = color_util.color_hs_to_RGB(*hs_color)
        elif ColorMode.RGBW in supported_color_modes:
            rgb_color = color_util.color_hs_to_RGB(*hs_color)
            params[ATTR_RGBW_COLOR] = color_util.color_rgb_to_rgbw(*rgb_color)
        elif ColorMode.RGBWW in supported_color_modes:
            rgb_color = color_util.color_hs_to_RGB(*hs_color)
            params[ATTR_RGBWW_COLOR] = color_util.color_rgb_to_rgbww(
                *rgb_color, light.min_color_temp_kelvin, light.max_color_temp_kelvin
            )
        elif ColorMode.XY in supported_color_modes:
            params[ATTR_XY_COLOR] = color_util.color_hs_to_xy(*hs_color)
        elif ColorMode.COLOR_TEMP in supported_color_modes:
            xy_color = color_util.color_hs_to_xy(*hs_color)
            params[ATTR_COLOR_TEMP_KELVIN] = color_util.color_xy_to_temperature(
                *xy_color
            )
    elif ATTR_RGB_COLOR in params and ColorMode.RGB not in supported_color_modes:
        rgb_color = params.pop(ATTR_RGB_COLOR)
        assert rgb_color is not None
        if TYPE_CHECKING:
            rgb_color = cast(tuple[int, int, int], rgb_color)
        if ColorMode.RGBW in supported_color_modes:
            params[ATTR_RGBW_COLOR] = color_util.color_rgb_to_rgbw(*rgb_color)
        elif ColorMode.RGBWW in supported_color_modes:
            params[ATTR_RGBWW_COLOR] = color_util.color_rgb_to_rgbww(
                *rgb_color,
                light.min_color_temp_kelvin,
                light.max_color_temp_kelvin,
            )
        elif ColorMode.HS in supported_color_modes:
            params[ATTR_HS_COLOR] = color_util.color_RGB_to_hs(*rgb_color)
        elif ColorMode.XY in supported_color_modes:
            params[ATTR_XY_COLOR] = color_util.color_RGB_to_xy(*rgb_color)
        elif ColorMode.COLOR_TEMP in supported_color_modes:
            xy_color = color_util.color_RGB_to_xy(*rgb_color)
            params[ATTR_COLOR_TEMP_KELVIN] = color_util.color_xy_to_temperature(
                *xy_color
            )
    elif ATTR_XY_COLOR in params and ColorMode.XY not in supported_color_modes:
        xy_color = params.pop(ATTR_XY_COLOR)
        if ColorMode.HS in supported_color_modes:
            params[ATTR_HS_COLOR] = color_util.color_xy_to_hs(*xy_color)
        elif ColorMode.RGB in supported_color_modes:
            params[ATTR_RGB_COLOR] = color_util.color_xy_to_RGB(*xy_color)
        elif ColorMode.RGBW in supported_color_modes:
            rgb_color = color_util.color_xy_to_RGB(*xy_color)
            params[ATTR_RGBW_COLOR] = color_util.color_rgb_to_rgbw(*rgb_color)
        elif ColorMode.RGBWW in supported_color_modes:
            rgb_color = color_util.color_xy_to_RGB(*xy_color)
            params[ATTR_RGBWW_COLOR] = color_util.color_rgb_to_rgbww(
                *rgb_color, light.min_color_temp_kelvin, light.max_color_temp_kelvin
            )
        elif ColorMode.COLOR_TEMP in supported_color_modes:
            params[ATTR_COLOR_TEMP_KELVIN] = color_util.color_xy_to_temperature(
                *xy_color
            )
    elif ATTR_RGBW_COLOR in params and ColorMode.RGBW not in supported_color_modes:
        rgbw_color = params.pop(ATTR_RGBW_COLOR)
        rgb_color = color_util.color_rgbw_to_rgb(*rgbw_color)
        if ColorMode.RGB in supported_color_modes:
            params[ATTR_RGB_COLOR] = rgb_color
        elif ColorMode.RGBWW in supported_color_modes:
            params[ATTR_RGBWW_COLOR] = color_util.color_rgb_to_rgbww(
                *rgb_color, light.min_color_temp_kelvin, light.max_color_temp_kelvin
            )
        elif ColorMode.HS in supported_color_modes:
            params[ATTR_HS_COLOR] = color_util.color_RGB_to_hs(*rgb_color)
        elif ColorMode.XY in supported_color_modes:
            params[ATTR_XY_COLOR] = color_util.color_RGB_to_xy(*rgb_color)
        elif ColorMode.COLOR_TEMP in supported_color_modes:
            xy_color = color_util.color_RGB_to_xy(*rgb_color)
            params[ATTR_COLOR_TEMP_KELVIN] = color_util.color_xy_to_temperature(
                *xy_color
            )
    elif ATTR_RGBWW_COLOR in params and ColorMode.RGBWW not in supported_color_modes:
        rgbww_color = params.pop(ATTR_RGBWW_COLOR)
        assert rgbww_color is not None
        if TYPE_CHECKING:
            rgbww_color = cast(tuple[int, int, int, int, int], rgbww_color)
        rgb_color = color_util.color_rgbww_to_rgb(
            *rgbww_color, light.min_color_temp_kelvin, light.max_color_temp_kelvin
        )
        if ColorMode.RGB in supported_color_modes:
            params[ATTR_RGB_COLOR] = rgb_color
        elif ColorMode.RGBW in supported_color_modes:
            params[ATTR_RGBW_COLOR] = color_util.color_rgb_to_rgbw(*rgb_color)
        elif ColorMode.HS in supported_color_modes:
            params[ATTR_HS_COLOR] = color_util.color_RGB_to_hs(*rgb_color)
        elif ColorMode.XY in supported_color_modes:
            params[ATTR_XY_COLOR] = color_util.color_RGB_to_xy(*rgb_color)
        elif ColorMode.COLOR_TEMP in supported_color_modes:
            xy_color = color_util.color_RGB_to_xy(*rgb_color)
            params[ATTR_COLOR_TEMP_KELVIN] = color_util.color_xy_to_temperature(
                *xy_color
            )

    # If white is set to True, set it to the light's brightness
    # Add a warning in Home Assistant Core 2024.3 if the brightness is set to an
    # integer.
    if params.get(ATTR_WHITE) is True:
        params[ATTR_WHITE] = light.brightness

    # If both white and brightness are specified, override white
    if ATTR_WHITE in params and ColorMode.WHITE in supported_color_modes:
        params[ATTR_WHITE] = params.pop(ATTR_BRIGHTNESS, params[ATTR_WHITE])

    return params