def __init__(self, *args: Any) -> None:
        """Initialize a new Light accessory object."""
        super().__init__(*args, category=CATEGORY_LIGHTBULB)
        self._reload_on_change_attrs.extend(
            (
                ATTR_SUPPORTED_COLOR_MODES,
                ATTR_MAX_COLOR_TEMP_KELVIN,
                ATTR_MIN_COLOR_TEMP_KELVIN,
            )
        )
        self.chars = []
        self._event_timer: CALLBACK_TYPE | None = None
        self._pending_events: dict[str, Any] = {}

        state = self.hass.states.get(self.entity_id)
        assert state
        attributes = state.attributes
        self.color_modes = color_modes = (
            attributes.get(ATTR_SUPPORTED_COLOR_MODES) or []
        )
        self._previous_color_mode = attributes.get(ATTR_COLOR_MODE)
        self.color_supported = color_supported(color_modes)
        self.color_temp_supported = color_temp_supported(color_modes)
        self.rgbw_supported = ColorMode.RGBW in color_modes
        self.rgbww_supported = ColorMode.RGBWW in color_modes
        self.white_supported = ColorMode.WHITE in color_modes
        self.brightness_supported = brightness_supported(color_modes)

        if self.brightness_supported:
            self.chars.append(CHAR_BRIGHTNESS)

        if self.color_supported:
            self.chars.extend([CHAR_HUE, CHAR_SATURATION])

        if self.color_temp_supported or COLOR_MODES_WITH_WHITES.intersection(
            self.color_modes
        ):
            self.chars.append(CHAR_COLOR_TEMPERATURE)

        serv_light = self.add_preload_service(SERV_LIGHTBULB, self.chars)
        self.char_on = serv_light.configure_char(CHAR_ON, value=0)

        if self.brightness_supported:
            # Initial value is set to 100 because 0 is a special value (off). 100 is
            # an arbitrary non-zero value. It is updated immediately by async_update_state
            # to set to the correct initial value.
            self.char_brightness = serv_light.configure_char(CHAR_BRIGHTNESS, value=100)

        if CHAR_COLOR_TEMPERATURE in self.chars:
            min_mireds = color_temperature_kelvin_to_mired(
                attributes.get(ATTR_MAX_COLOR_TEMP_KELVIN, DEFAULT_MAX_COLOR_TEMP)
            )
            max_mireds = color_temperature_kelvin_to_mired(
                attributes.get(ATTR_MIN_COLOR_TEMP_KELVIN, DEFAULT_MIN_COLOR_TEMP)
            )
            # Ensure min is less than max
            self.min_mireds, self.max_mireds = get_min_max(min_mireds, max_mireds)
            if not self.color_temp_supported and not self.rgbww_supported:
                self.max_mireds = self.min_mireds
            self.char_color_temp = serv_light.configure_char(
                CHAR_COLOR_TEMPERATURE,
                value=self.min_mireds,
                properties={
                    PROP_MIN_VALUE: self.min_mireds,
                    PROP_MAX_VALUE: self.max_mireds,
                },
            )

        if self.color_supported:
            self.char_hue = serv_light.configure_char(CHAR_HUE, value=0)
            self.char_saturation = serv_light.configure_char(CHAR_SATURATION, value=75)

        self.async_update_state(state)
        serv_light.setter_callback = self._set_chars