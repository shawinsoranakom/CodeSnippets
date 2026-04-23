def __init__(
        self,
        device: CustomerDevice,
        device_manager: Manager,
        description: TuyaLightEntityDescription,
        definition: TuyaLightDefinition,
    ) -> None:
        """Init TuyaHaLight."""
        super().__init__(device, device_manager, description)
        self._brightness_wrapper = definition.brightness_wrapper
        self._color_data_wrapper = definition.color_data_wrapper
        self._color_mode_wrapper = definition.color_mode_wrapper
        self._color_temp_wrapper = definition.color_temp_wrapper
        self._switch_wrapper = definition.switch_wrapper

        color_modes: set[ColorMode] = {ColorMode.ONOFF}

        if definition.brightness_wrapper:
            color_modes.add(ColorMode.BRIGHTNESS)

        if definition.color_data_wrapper:
            color_modes.add(ColorMode.HS)

        # Check if the light has color temperature
        if definition.color_temp_wrapper:
            color_modes.add(ColorMode.COLOR_TEMP)
        # If light has color but does not have color_temp, check if it has
        # work_mode "white"
        elif (
            color_supported(color_modes)
            and definition.color_mode_wrapper is not None
            and WorkMode.WHITE in definition.color_mode_wrapper.options
        ):
            color_modes.add(ColorMode.WHITE)
            self._white_color_mode = ColorMode.WHITE

        self._attr_supported_color_modes = filter_supported_color_modes(color_modes)
        if len(self._attr_supported_color_modes) == 1:
            # If the light supports only a single color mode, set it now
            self._fixed_color_mode = next(iter(self._attr_supported_color_modes))