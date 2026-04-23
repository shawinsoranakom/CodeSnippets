def _get_activity(self) -> LawnMowerActivity | None:
        """Return the current lawn mower activity."""
        if self.coordinator.data is None:
            return None

        state = self.coordinator.data["state"]
        activity = self.coordinator.data["activity"]

        if state is None or activity is None:
            return None

        if state == MowerState.PAUSED:
            return LawnMowerActivity.PAUSED
        if state in (MowerState.STOPPED, MowerState.OFF, MowerState.WAIT_FOR_SAFETYPIN):
            # This is actually stopped, but that isn't an option
            return LawnMowerActivity.ERROR
        if state == MowerState.PENDING_START and activity == MowerActivity.NONE:
            # This happens when the mower is safety stopped and we try to send a
            # command to start it.
            return LawnMowerActivity.ERROR
        if state in (
            MowerState.RESTRICTED,
            MowerState.IN_OPERATION,
            MowerState.PENDING_START,
        ):
            if activity in (
                MowerActivity.CHARGING,
                MowerActivity.PARKED,
                MowerActivity.NONE,
            ):
                return LawnMowerActivity.DOCKED
            if activity in (MowerActivity.GOING_OUT, MowerActivity.MOWING):
                return LawnMowerActivity.MOWING
            if activity == MowerActivity.GOING_HOME:
                return LawnMowerActivity.RETURNING
        return LawnMowerActivity.ERROR