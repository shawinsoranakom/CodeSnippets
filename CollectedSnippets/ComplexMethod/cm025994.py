def find_hsbk(hass: HomeAssistant, **kwargs: Any) -> list[float | int | None] | None:
    """Find the desired color from a number of possible inputs.

    Hue, Saturation, Brightness, Kelvin
    """
    hue, saturation, brightness, kelvin = [None] * 4

    if (color_name := kwargs.get(ATTR_COLOR_NAME)) is not None:
        try:
            hue, saturation = color_util.color_RGB_to_hs(
                *color_util.color_name_to_rgb(color_name)
            )
        except ValueError:
            _LOGGER.warning(
                "Got unknown color %s, falling back to neutral white", color_name
            )
            hue, saturation = (0, 0)

    if ATTR_HS_COLOR in kwargs:
        hue, saturation = kwargs[ATTR_HS_COLOR]
    elif ATTR_RGB_COLOR in kwargs:
        hue, saturation = color_util.color_RGB_to_hs(*kwargs[ATTR_RGB_COLOR])
    elif ATTR_XY_COLOR in kwargs:
        hue, saturation = color_util.color_xy_to_hs(*kwargs[ATTR_XY_COLOR])

    if hue is not None:
        assert saturation is not None
        hue = int(hue / 360 * 65535)
        saturation = int(saturation / 100 * 65535)
        kelvin = 3500

    if ATTR_COLOR_TEMP_KELVIN in kwargs:
        kelvin = kwargs.pop(ATTR_COLOR_TEMP_KELVIN)
        saturation = 0

    if ATTR_BRIGHTNESS in kwargs:
        brightness = convert_8_to_16(kwargs[ATTR_BRIGHTNESS])

    if ATTR_BRIGHTNESS_PCT in kwargs:
        brightness = convert_8_to_16(round(255 * kwargs[ATTR_BRIGHTNESS_PCT] / 100))

    hsbk = [hue, saturation, brightness, kelvin]
    return None if hsbk == [None] * 4 else hsbk