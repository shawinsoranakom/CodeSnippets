def __init__(
        self,
        device: CustomerDevice,
        device_manager: Manager,
        description: TuyaCoverEntityDescription,
        definition: TuyaCoverDefinition,
    ) -> None:
        """Init Tuya Cover."""
        super().__init__(device, device_manager, description)
        self._attr_supported_features = CoverEntityFeature(0)

        self._current_position = (
            definition.current_position_wrapper or definition.set_position_wrapper
        )
        self._current_state_wrapper = definition.current_state_wrapper
        self._instruction_wrapper = definition.instruction_wrapper
        self._set_position = definition.set_position_wrapper
        self._tilt_position = definition.tilt_position_wrapper

        if definition.instruction_wrapper:
            if TuyaCoverAction.OPEN in definition.instruction_wrapper.options:
                self._attr_supported_features |= CoverEntityFeature.OPEN
            if TuyaCoverAction.CLOSE in definition.instruction_wrapper.options:
                self._attr_supported_features |= CoverEntityFeature.CLOSE
            if TuyaCoverAction.STOP in definition.instruction_wrapper.options:
                self._attr_supported_features |= CoverEntityFeature.STOP

        if definition.set_position_wrapper:
            self._attr_supported_features |= CoverEntityFeature.SET_POSITION
        if definition.tilt_position_wrapper:
            self._attr_supported_features |= CoverEntityFeature.SET_TILT_POSITION