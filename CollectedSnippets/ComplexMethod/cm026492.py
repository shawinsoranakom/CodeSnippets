def get_property(self, name: str) -> Any:
        """Read and return a property."""
        if name != "mode":
            raise UnsupportedProperty(name)

        # Fan Direction
        if self.instance == f"{fan.DOMAIN}.{fan.ATTR_DIRECTION}":
            mode = self.entity.attributes.get(fan.ATTR_DIRECTION, None)
            if mode in (fan.DIRECTION_FORWARD, fan.DIRECTION_REVERSE, STATE_UNKNOWN):
                return f"{fan.ATTR_DIRECTION}.{mode}"

        # Fan preset_mode
        if self.instance == f"{fan.DOMAIN}.{fan.ATTR_PRESET_MODE}":
            mode = self.entity.attributes.get(fan.ATTR_PRESET_MODE, None)
            if mode in self.entity.attributes.get(fan.ATTR_PRESET_MODES, ()):
                return f"{fan.ATTR_PRESET_MODE}.{mode}"

        # Humidifier mode
        if self.instance == f"{humidifier.DOMAIN}.{humidifier.ATTR_MODE}":
            mode = self.entity.attributes.get(humidifier.ATTR_MODE)
            modes: list[str] = (
                self.entity.attributes.get(humidifier.ATTR_AVAILABLE_MODES) or []
            )
            if mode in modes:
                return f"{humidifier.ATTR_MODE}.{mode}"

        # Remote Activity
        if self.instance == f"{remote.DOMAIN}.{remote.ATTR_ACTIVITY}":
            activity = self.entity.attributes.get(remote.ATTR_CURRENT_ACTIVITY, None)
            if activity in self.entity.attributes.get(remote.ATTR_ACTIVITY_LIST, []):
                return f"{remote.ATTR_ACTIVITY}.{activity}"

        # Water heater operation mode
        if self.instance == f"{water_heater.DOMAIN}.{water_heater.ATTR_OPERATION_MODE}":
            operation_mode = self.entity.attributes.get(
                water_heater.ATTR_OPERATION_MODE
            )
            operation_modes: list[str] = (
                self.entity.attributes.get(water_heater.ATTR_OPERATION_LIST) or []
            )
            if operation_mode in operation_modes:
                return f"{water_heater.ATTR_OPERATION_MODE}.{operation_mode}"

        # Cover Position
        if self.instance == f"{cover.DOMAIN}.{cover.ATTR_POSITION}":
            # Return state instead of position when using ModeController.
            mode = self.entity.state
            if mode in (
                cover.CoverState.OPEN,
                cover.CoverState.OPENING,
                cover.CoverState.CLOSED,
                cover.CoverState.CLOSING,
                STATE_UNKNOWN,
            ):
                return f"{cover.ATTR_POSITION}.{mode}"

        # Valve position state
        if self.instance == f"{valve.DOMAIN}.state":
            # Return state instead of position when using ModeController.
            state = self.entity.state
            if state in (
                valve.STATE_OPEN,
                valve.STATE_OPENING,
                valve.STATE_CLOSED,
                valve.STATE_CLOSING,
                STATE_UNKNOWN,
            ):
                return f"state.{state}"

        return None