def alarm_state(self) -> AlarmControlPanelState | None:
        """Return the state of the device."""
        state: AlarmControlPanelState | None = None
        if self._partition.arming_state.is_disarmed():
            state = AlarmControlPanelState.DISARMED
        elif self._partition.arming_state.is_armed_night():
            state = AlarmControlPanelState.ARMED_NIGHT
        elif self._partition.arming_state.is_armed_home():
            state = AlarmControlPanelState.ARMED_HOME
        elif self._partition.arming_state.is_armed_away():
            state = AlarmControlPanelState.ARMED_AWAY
        elif self._partition.arming_state.is_armed_custom_bypass():
            state = AlarmControlPanelState.ARMED_CUSTOM_BYPASS
        elif self._partition.arming_state.is_arming():
            state = AlarmControlPanelState.ARMING
        elif self._partition.arming_state.is_disarming():
            state = AlarmControlPanelState.DISARMING
        elif (
            self._partition.arming_state.is_triggered_police()
            or self._partition.arming_state.is_triggered_fire()
            or self._partition.arming_state.is_triggered_gas()
        ):
            state = AlarmControlPanelState.TRIGGERED

        return state