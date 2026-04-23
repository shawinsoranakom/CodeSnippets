def __init__(self, ih_device_id, ih_device, controller):
        """Initialize the thermostat."""
        self._controller = controller
        self._device_id = ih_device_id
        self._ih_device = ih_device
        self._attr_name = ih_device.get("name")
        self._device_type = controller.device_type
        self._connected = None
        self._attr_hvac_modes = []
        self._outdoor_temp = None
        self._hvac_mode = None
        self._run_hours = None
        self._rssi = None
        self._attr_swing_modes = [SWING_OFF]
        self._vvane = None
        self._hvane = None
        self._power = False
        self._power_consumption_heat = None
        self._power_consumption_cool = None

        # Setpoint support
        if controller.has_setpoint_control(ih_device_id):
            self._attr_supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE

        # Setup swing list
        if controller.has_vertical_swing(ih_device_id):
            self._attr_swing_modes.append(SWING_VERTICAL)
        if controller.has_horizontal_swing(ih_device_id):
            self._attr_swing_modes.append(SWING_HORIZONTAL)
        if (
            SWING_HORIZONTAL in self._attr_swing_modes
            and SWING_VERTICAL in self._attr_swing_modes
        ):
            self._attr_swing_modes.append(SWING_BOTH)
        if len(self._attr_swing_modes) > 1:
            self._attr_supported_features |= ClimateEntityFeature.SWING_MODE

        # Setup fan speeds
        self._attr_fan_modes = controller.get_fan_speed_list(ih_device_id)
        if self._attr_fan_modes:
            self._attr_supported_features |= ClimateEntityFeature.FAN_MODE

        # Preset support
        if ih_device.get("climate_working_mode"):
            self._attr_supported_features |= ClimateEntityFeature.PRESET_MODE

        # Setup HVAC modes
        if modes := controller.get_mode_list(ih_device_id):
            mode_list = [MAP_IH_TO_HVAC_MODE[mode] for mode in modes]
            self._attr_hvac_modes.extend(mode_list)
        self._attr_hvac_modes.append(HVACMode.OFF)

        if len(self.hvac_modes) > 1:
            self._attr_supported_features |= (
                ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON
            )