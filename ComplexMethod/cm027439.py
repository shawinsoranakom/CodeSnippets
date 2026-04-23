def __init__(self, data: BSBLanData) -> None:
        """Initialize BSBLAN water heater."""
        super().__init__(data.fast_coordinator, data.slow_coordinator, data)
        self._attr_unique_id = format_mac(data.device.MAC)

        # Set temperature unit
        self._attr_temperature_unit = data.fast_coordinator.client.get_temperature_unit
        # Initialize available attribute to resolve multiple inheritance conflict
        self._attr_available = True

        # Set temperature limits based on device capabilities from slow coordinator
        dhw_config = (
            data.slow_coordinator.data.dhw_config
            if data.slow_coordinator.data
            else None
        )

        # For min_temp: Use reduced_setpoint from config data (slow polling)
        if (
            dhw_config is not None
            and dhw_config.reduced_setpoint is not None
            and dhw_config.reduced_setpoint.value is not None
        ):
            self._attr_min_temp = dhw_config.reduced_setpoint.value
        else:
            self._attr_min_temp = 10.0  # Default minimum

        # For max_temp: Use nominal_setpoint_max from config data (slow polling)
        if (
            dhw_config is not None
            and dhw_config.nominal_setpoint_max is not None
            and dhw_config.nominal_setpoint_max.value is not None
        ):
            self._attr_max_temp = dhw_config.nominal_setpoint_max.value
        else:
            self._attr_max_temp = 65.0