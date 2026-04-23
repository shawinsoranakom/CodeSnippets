def _update_from_device(self) -> None:
        """Update from device."""
        self._calculate_features()
        self._attr_is_opening = False
        self._attr_is_closing = False

        current_state: int | None
        current_state = self.get_matter_attribute_value(
            ValveConfigurationAndControl.Attributes.CurrentState
        )
        target_state: int | None
        target_state = self.get_matter_attribute_value(
            ValveConfigurationAndControl.Attributes.TargetState
        )

        if current_state is None:
            self._attr_is_closed = None
        elif current_state == ValveStateEnum.kTransitioning and (
            target_state == ValveStateEnum.kOpen
        ):
            self._attr_is_opening = True
            self._attr_is_closed = None
        elif current_state == ValveStateEnum.kTransitioning and (
            target_state == ValveStateEnum.kClosed
        ):
            self._attr_is_closing = True
            self._attr_is_closed = None
        elif current_state == ValveStateEnum.kClosed:
            self._attr_is_closed = True
        elif current_state == ValveStateEnum.kOpen:
            self._attr_is_closed = False
        else:
            self._attr_is_closed = None

        # handle optional position
        if self.supported_features & ValveEntityFeature.SET_POSITION:
            self._attr_current_valve_position = self.get_matter_attribute_value(
                ValveConfigurationAndControl.Attributes.CurrentLevel
            )