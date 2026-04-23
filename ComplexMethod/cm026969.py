def __init__(
        self, config_entry: ZwaveJSConfigEntry, driver: Driver, info: ZwaveDiscoveryInfo
    ) -> None:
        """Initialize."""
        super().__init__(config_entry, driver, info)
        pos_value: ZwaveValue | None = None
        tilt_value: ZwaveValue | None = None
        self._up_value = cast(
            ZwaveValue,
            self.get_zwave_value(
                WINDOW_COVERING_LEVEL_CHANGE_UP_PROPERTY,
                value_property_key=info.primary_value.property_key,
            ),
        )
        self._down_value = cast(
            ZwaveValue,
            self.get_zwave_value(
                WINDOW_COVERING_LEVEL_CHANGE_DOWN_PROPERTY,
                value_property_key=info.primary_value.property_key,
            ),
        )

        # If primary value is for position, we have to search for a tilt value
        if info.primary_value.property_key in COVER_POSITION_PROPERTY_KEYS:
            pos_value = info.primary_value
            tilt_value = next(
                (
                    value
                    for property_key in COVER_TILT_PROPERTY_KEYS
                    if (
                        value := self.get_zwave_value(
                            CURRENT_VALUE_PROPERTY, value_property_key=property_key
                        )
                    )
                ),
                None,
            )
        # If primary value is for tilt, there is no position value
        else:
            tilt_value = info.primary_value

        # Set position and tilt values if they exist. If the corresponding value is of
        # the type No Position, we remove the corresponding set position feature.
        for set_values_func, value, set_position_feature in (
            (self._set_position_values, pos_value, CoverEntityFeature.SET_POSITION),
            (self._set_tilt_values, tilt_value, CoverEntityFeature.SET_TILT_POSITION),
        ):
            if value:
                set_values_func(
                    value,
                    stop_value=self.get_zwave_value(
                        WINDOW_COVERING_LEVEL_CHANGE_UP_PROPERTY,
                        value_property_key=value.property_key,
                    ),
                )
                if value.property_key in NO_POSITION_PROPERTY_KEYS:
                    assert self._attr_supported_features
                    self._attr_supported_features ^= set_position_feature

        additional_info: list[str] = [
            value.property_key_name.removesuffix(f" {NO_POSITION_SUFFIX}")
            for value in (self._current_position_value, self._current_tilt_value)
            if value and value.property_key_name
        ]
        self._attr_name = self.generate_name(additional_info=additional_info)
        self._attr_device_class = CoverDeviceClass.WINDOW