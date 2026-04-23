def __init__(
        self, config_entry: ZwaveJSConfigEntry, driver: Driver, info: ZwaveDiscoveryInfo
    ) -> None:
        """Initialize the light."""
        super().__init__(config_entry, driver, info)
        self._supports_color = False
        self._supports_rgbw = False
        self._supports_color_temp = False
        self._supports_dimming = False
        self._warm_white = self.get_zwave_value(
            TARGET_COLOR_PROPERTY,
            CommandClass.SWITCH_COLOR,
            value_property_key=ColorComponent.WARM_WHITE,
        )
        self._cold_white = self.get_zwave_value(
            TARGET_COLOR_PROPERTY,
            CommandClass.SWITCH_COLOR,
            value_property_key=ColorComponent.COLD_WHITE,
        )

        self._target_brightness: Value | None = None

        # get additional (optional) values and set features
        if self.info.primary_value.command_class == CommandClass.SWITCH_BINARY:
            # This light can not be dimmed separately from the color channels
            self._target_brightness = self.get_zwave_value(
                TARGET_VALUE_PROPERTY,
                CommandClass.SWITCH_BINARY,
                add_to_watched_value_ids=False,
            )
            self._supports_dimming = False
        elif self.info.primary_value.command_class == CommandClass.SWITCH_MULTILEVEL:
            # This light can be dimmed separately from the color channels
            self._target_brightness = self.get_zwave_value(
                TARGET_VALUE_PROPERTY,
                CommandClass.SWITCH_MULTILEVEL,
                add_to_watched_value_ids=False,
            )
            self._supports_dimming = True
        elif self.info.primary_value.command_class == CommandClass.BASIC:
            # If the command class is Basic, we must generate a name that includes
            # the command class name to avoid ambiguity
            self._attr_name = self.generate_name(
                include_value_name=True, alternate_value_name="Basic"
            )
            self._target_brightness = self.get_zwave_value(
                TARGET_VALUE_PROPERTY,
                CommandClass.BASIC,
                add_to_watched_value_ids=False,
            )
            self._supports_dimming = True

        self._current_color = self.get_zwave_value(
            CURRENT_COLOR_PROPERTY,
            CommandClass.SWITCH_COLOR,
            value_property_key=None,
        )
        self._target_color = self.get_zwave_value(
            TARGET_COLOR_PROPERTY,
            CommandClass.SWITCH_COLOR,
            add_to_watched_value_ids=False,
        )

        self._calculate_color_support()
        self._attr_supported_color_modes = set()
        if self._supports_rgbw:
            self._attr_supported_color_modes.add(ColorMode.RGBW)
        elif self._supports_color:
            self._attr_supported_color_modes.add(ColorMode.HS)
        if self._supports_color_temp:
            self._attr_supported_color_modes.add(ColorMode.COLOR_TEMP)
        if not self._attr_supported_color_modes:
            if self.info.primary_value.command_class == CommandClass.SWITCH_BINARY:
                self._attr_supported_color_modes.add(ColorMode.ONOFF)
            else:
                self._attr_supported_color_modes.add(ColorMode.BRIGHTNESS)
        self._calculate_color_values()

        # Entity class attributes
        self.supports_brightness_transition = bool(
            self._target_brightness is not None
            and TRANSITION_DURATION_OPTION
            in self._target_brightness.metadata.value_change_options
        )
        self.supports_color_transition = bool(
            self._target_color is not None
            and TRANSITION_DURATION_OPTION
            in self._target_color.metadata.value_change_options
        )

        if self.supports_brightness_transition or self.supports_color_transition:
            self._attr_supported_features |= LightEntityFeature.TRANSITION

        self._set_optimistic_state: bool = False