def alarm_state(self) -> AlarmControlPanelState | None:
        """Return the state of the device."""
        if self._partition.triggered:
            return AlarmControlPanelState.TRIGGERED
        if self._partition.arming:
            return AlarmControlPanelState.ARMING
        if self._partition.disarmed:
            return AlarmControlPanelState.DISARMED
        if self._partition.armed:
            return self._risco_to_ha[RISCO_ARM]
        if self._partition.partially_armed:
            for group, armed in self._partition.groups.items():
                if armed:
                    return self._risco_to_ha[group]

            return self._risco_to_ha[RISCO_PARTIAL_ARM]

        return None