def __init__(
        self,
        config_entry: ZwaveJSConfigEntry,
        driver: Driver,
        info: ZwaveDiscoveryInfo,
    ) -> None:
        """Initialize a ZWaveCover entity."""
        super().__init__(config_entry, driver, info)
        self._set_position_values(
            self.info.primary_value,
            stop_value=(
                self.get_zwave_value(COVER_OPEN_PROPERTY)
                or self.get_zwave_value(COVER_UP_PROPERTY)
                or self.get_zwave_value(COVER_ON_PROPERTY)
            ),
        )

        # Multilevel Switch CC v3 and earlier don't report targetValue,
        # so we cannot determine when the cover stops moving,
        # especially when the device is controlled physically.
        # OPENING/CLOSING states must not be used for these devices,
        # because they will become stale/incorrect.
        if (
            self.info.primary_value.command_class == CommandClass.SWITCH_MULTILEVEL
            and self.info.primary_value.cc_version < 4
        ):
            self._moving_state_disabled = True

        # Entity class attributes
        self._attr_device_class = CoverDeviceClass.WINDOW
        if (
            isinstance(self.info, ZwaveDiscoveryInfo)
            and self.info.platform_hint
            and self.info.platform_hint.startswith("shutter")
        ):
            self._attr_device_class = CoverDeviceClass.SHUTTER
        elif (
            isinstance(self.info, ZwaveDiscoveryInfo)
            and self.info.platform_hint
            and self.info.platform_hint.startswith("blind")
        ):
            self._attr_device_class = CoverDeviceClass.BLIND
        elif (
            isinstance(self.info, ZwaveDiscoveryInfo)
            and self.info.platform_hint
            and self.info.platform_hint.startswith("gate")
        ):
            self._attr_device_class = CoverDeviceClass.GATE