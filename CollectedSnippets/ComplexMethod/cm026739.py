def alarm_state(self) -> AlarmControlPanelState | None:
        """Return the state of the device."""
        state = None

        if self._info["status"]["alarm"]:
            state = AlarmControlPanelState.TRIGGERED
        elif self._info["status"]["armed_zero_entry_delay"]:
            state = AlarmControlPanelState.ARMED_NIGHT
        elif self._info["status"]["armed_away"]:
            state = AlarmControlPanelState.ARMED_AWAY
        elif self._info["status"]["armed_stay"]:
            state = AlarmControlPanelState.ARMED_HOME
        elif self._info["status"]["exit_delay"]:
            state = AlarmControlPanelState.ARMING
        elif self._info["status"]["entry_delay"]:
            state = AlarmControlPanelState.PENDING
        elif self._info["status"]["alpha"]:
            state = AlarmControlPanelState.DISARMED
        return state