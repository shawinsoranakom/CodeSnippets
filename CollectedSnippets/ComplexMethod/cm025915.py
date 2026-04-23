def __init__(self, controller: Controller) -> None:
        """Initialise ControllerDevice."""
        self._controller = controller

        self._attr_supported_features = (
            ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TURN_ON
        )

        # Typically, iZone will automatically set the controller's target
        # temperature; but there are situations where Home Assistant should be
        # allowed to set it:
        #
        # 1. The controller is in RAS mode (i.e., not in master/slave mode).
        # 2. The controller is in master mode, but the control zone is set to
        #    zone 13 (i.e., the master unit itself), or an invalid zone
        #    (greater than the total number of zones). In this case, the
        #    master unit is controlling the temperature directly.
        # 3. Any of the zones do not have a temperature sensor
        if (
            controller.ras_mode == "RAS"
            or (
                controller.ras_mode == "master"
                and controller.zone_ctrl > controller.zones_total
            )
            or any(zone.temp_current is None for zone in controller.zones)
        ):
            self._attr_supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE

        self._state_to_pizone = {
            HVACMode.COOL: Controller.Mode.COOL,
            HVACMode.HEAT: Controller.Mode.HEAT,
            HVACMode.HEAT_COOL: Controller.Mode.AUTO,
            HVACMode.FAN_ONLY: Controller.Mode.VENT,
            HVACMode.DRY: Controller.Mode.DRY,
        }
        if controller.free_air_enabled:
            self._attr_supported_features |= ClimateEntityFeature.PRESET_MODE

        self._fan_to_pizone = {}
        for fan in controller.fan_modes:
            self._fan_to_pizone[_IZONE_FAN_TO_HA[fan]] = fan

        self._attr_unique_id = controller.device_uid
        self._attr_device_info = DeviceInfo(
            identifiers={(IZONE, controller.device_uid)},
            manufacturer="IZone",
            model=controller.sys_type,
            name=f"iZone Controller {controller.device_uid}",
        )

        # Create the zones
        self.zones = {}
        for zone in controller.zones:
            self.zones[zone] = ZoneDevice(self, zone)