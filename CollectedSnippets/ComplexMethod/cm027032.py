def __init__(self, fibaro_device: DeviceModel) -> None:
        """Initialize the light."""
        supports_color = (
            "color" in fibaro_device.properties
            or "colorComponents" in fibaro_device.properties
            or "RGB" in fibaro_device.type
            or "rgb" in fibaro_device.type
            or "color" in fibaro_device.base_type
        ) and (
            "setColor" in fibaro_device.actions
            or "setColorComponents" in fibaro_device.actions
        )
        supports_white_v = (
            "setW" in fibaro_device.actions
            or "RGBW" in fibaro_device.type
            or "rgbw" in fibaro_device.type
        )
        supports_dimming = (
            fibaro_device.has_interface("levelChange")
            or fibaro_device.type == "com.fibaro.multilevelSwitch"
        ) and "setValue" in fibaro_device.actions

        if supports_color and supports_white_v:
            self._attr_supported_color_modes = {ColorMode.RGBW}
            self._attr_color_mode = ColorMode.RGBW
        elif supports_color:
            self._attr_supported_color_modes = {ColorMode.RGB}
            self._attr_color_mode = ColorMode.RGB
        elif supports_dimming:
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
            self._attr_color_mode = ColorMode.BRIGHTNESS
        else:
            self._attr_supported_color_modes = {ColorMode.ONOFF}
            self._attr_color_mode = ColorMode.ONOFF

        super().__init__(fibaro_device)
        self.entity_id = ENTITY_ID_FORMAT.format(self.ha_id)