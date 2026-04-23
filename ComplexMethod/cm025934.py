def _create_ui_light(xknx: XKNX, knx_config: ConfigType, name: str) -> XknxLight:
    """Return a KNX Light device to be used within XKNX."""

    conf = ConfigExtractor(knx_config)

    group_address_tunable_white = None
    group_address_tunable_white_state = None
    group_address_color_temp = None
    group_address_color_temp_state = None

    color_temperature_type = ColorTemperatureType.UINT_2_BYTE
    if _color_temp_dpt := conf.get_dpt(CONF_GA_COLOR_TEMP):
        if _color_temp_dpt == ColorTempModes.RELATIVE.value:
            group_address_tunable_white = conf.get_write(CONF_GA_COLOR_TEMP)
            group_address_tunable_white_state = conf.get_state_and_passive(
                CONF_GA_COLOR_TEMP
            )
        else:
            # absolute uint or float
            group_address_color_temp = conf.get_write(CONF_GA_COLOR_TEMP)
            group_address_color_temp_state = conf.get_state_and_passive(
                CONF_GA_COLOR_TEMP
            )
            if _color_temp_dpt == ColorTempModes.ABSOLUTE_FLOAT.value:
                color_temperature_type = ColorTemperatureType.FLOAT_2_BYTE

    color_dpt = conf.get_dpt(CONF_COLOR, CONF_GA_COLOR)

    return XknxLight(
        xknx,
        name=name,
        group_address_switch=conf.get_write(CONF_GA_SWITCH),
        group_address_switch_state=conf.get_state_and_passive(CONF_GA_SWITCH),
        group_address_brightness=conf.get_write(CONF_GA_BRIGHTNESS),
        group_address_brightness_state=conf.get_state_and_passive(CONF_GA_BRIGHTNESS),
        group_address_color=(
            conf.get_write(CONF_COLOR, CONF_GA_COLOR)
            if color_dpt == LightColorMode.RGB
            else None
        ),
        group_address_color_state=(
            conf.get_state_and_passive(CONF_COLOR, CONF_GA_COLOR)
            if color_dpt == LightColorMode.RGB
            else None
        ),
        group_address_rgbw=(
            conf.get_write(CONF_COLOR, CONF_GA_COLOR)
            if color_dpt == LightColorMode.RGBW
            else None
        ),
        group_address_rgbw_state=(
            conf.get_state_and_passive(CONF_COLOR, CONF_GA_COLOR)
            if color_dpt == LightColorMode.RGBW
            else None
        ),
        group_address_hue=conf.get_write(CONF_COLOR, CONF_GA_HUE),
        group_address_hue_state=conf.get_state_and_passive(CONF_COLOR, CONF_GA_HUE),
        group_address_saturation=conf.get_write(CONF_COLOR, CONF_GA_SATURATION),
        group_address_saturation_state=conf.get_state_and_passive(
            CONF_COLOR, CONF_GA_SATURATION
        ),
        group_address_xyy_color=(
            conf.get_write(CONF_COLOR, CONF_GA_COLOR)
            if color_dpt == LightColorMode.XYY
            else None
        ),
        group_address_xyy_color_state=(
            conf.get_state_and_passive(CONF_COLOR, CONF_GA_COLOR)
            if color_dpt == LightColorMode.XYY
            else None
        ),
        group_address_tunable_white=group_address_tunable_white,
        group_address_tunable_white_state=group_address_tunable_white_state,
        group_address_color_temperature=group_address_color_temp,
        group_address_color_temperature_state=group_address_color_temp_state,
        group_address_switch_red=conf.get_write(CONF_COLOR, CONF_GA_RED_SWITCH),
        group_address_switch_red_state=conf.get_state_and_passive(
            CONF_COLOR, CONF_GA_RED_SWITCH
        ),
        group_address_brightness_red=conf.get_write(CONF_COLOR, CONF_GA_RED_BRIGHTNESS),
        group_address_brightness_red_state=conf.get_state_and_passive(
            CONF_COLOR, CONF_GA_RED_BRIGHTNESS
        ),
        group_address_switch_green=conf.get_write(CONF_COLOR, CONF_GA_GREEN_SWITCH),
        group_address_switch_green_state=conf.get_state_and_passive(
            CONF_COLOR, CONF_GA_GREEN_SWITCH
        ),
        group_address_brightness_green=conf.get_write(
            CONF_COLOR, CONF_GA_GREEN_BRIGHTNESS
        ),
        group_address_brightness_green_state=conf.get_state_and_passive(
            CONF_COLOR, CONF_GA_GREEN_BRIGHTNESS
        ),
        group_address_switch_blue=conf.get_write(CONF_COLOR, CONF_GA_BLUE_SWITCH),
        group_address_switch_blue_state=conf.get_state_and_passive(
            CONF_COLOR, CONF_GA_BLUE_SWITCH
        ),
        group_address_brightness_blue=conf.get_write(
            CONF_COLOR, CONF_GA_BLUE_BRIGHTNESS
        ),
        group_address_brightness_blue_state=conf.get_state_and_passive(
            CONF_COLOR, CONF_GA_BLUE_BRIGHTNESS
        ),
        group_address_switch_white=conf.get_write(CONF_COLOR, CONF_GA_WHITE_SWITCH),
        group_address_switch_white_state=conf.get_state_and_passive(
            CONF_COLOR, CONF_GA_WHITE_SWITCH
        ),
        group_address_brightness_white=conf.get_write(
            CONF_COLOR, CONF_GA_WHITE_BRIGHTNESS
        ),
        group_address_brightness_white_state=conf.get_state_and_passive(
            CONF_COLOR, CONF_GA_WHITE_BRIGHTNESS
        ),
        color_temperature_type=color_temperature_type,
        min_kelvin=knx_config[CONF_COLOR_TEMP_MIN],
        max_kelvin=knx_config[CONF_COLOR_TEMP_MAX],
        sync_state=knx_config[CONF_SYNC_STATE],
    )