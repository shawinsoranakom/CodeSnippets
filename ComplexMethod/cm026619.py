def __init__(
        self,
        device: CustomerDevice,
        device_manager: Manager,
        description: StateVacuumEntityDescription,
        definition: TuyaVacuumDefinition,
    ) -> None:
        """Init Tuya vacuum."""
        super().__init__(device, device_manager, description)
        self._action_wrapper = definition.action_wrapper
        self._activity_wrapper = definition.activity_wrapper
        self._fan_speed_wrapper = definition.fan_speed_wrapper

        self._attr_fan_speed_list = []
        self._attr_supported_features = VacuumEntityFeature.SEND_COMMAND

        if definition.action_wrapper:
            if TuyaVacuumAction.PAUSE in definition.action_wrapper.options:
                self._attr_supported_features |= VacuumEntityFeature.PAUSE
            if TuyaVacuumAction.RETURN_TO_BASE in definition.action_wrapper.options:
                self._attr_supported_features |= VacuumEntityFeature.RETURN_HOME
            if TuyaVacuumAction.LOCATE in definition.action_wrapper.options:
                self._attr_supported_features |= VacuumEntityFeature.LOCATE
            if TuyaVacuumAction.START in definition.action_wrapper.options:
                self._attr_supported_features |= VacuumEntityFeature.START
            if TuyaVacuumAction.STOP in definition.action_wrapper.options:
                self._attr_supported_features |= VacuumEntityFeature.STOP

        if definition.activity_wrapper:
            self._attr_supported_features |= VacuumEntityFeature.STATE

        if definition.fan_speed_wrapper:
            self._attr_fan_speed_list = definition.fan_speed_wrapper.options
            self._attr_supported_features |= VacuumEntityFeature.FAN_SPEED