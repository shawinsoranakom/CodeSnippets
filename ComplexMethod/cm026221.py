async def async_start_activity(self, activity: str) -> None:
        """Start an activity from the Harmony device."""

        if not activity:
            _LOGGER.error("%s: No activity specified with turn_on service", self.name)
            return

        activity_id = None
        activity_name = None

        if activity.isdigit() or activity == "-1":
            _LOGGER.debug("%s: Activity is numeric", self.name)
            activity_name = self._client.get_activity_name(int(activity))
            if activity_name:
                activity_id = activity

        if activity_id is None:
            _LOGGER.debug("%s: Find activity ID based on name", self.name)
            activity_name = str(activity)
            activity_id = self._client.get_activity_id(activity_name)

        if activity_id is None:
            _LOGGER.error("%s: Activity %s is invalid", self.name, activity)
            return

        _, current_activity_name = self.current_activity
        if current_activity_name == activity_name:
            # Automations or HomeKit may turn the device on multiple times
            # when the current activity is already active which will cause
            # harmony to loose state.  This behavior is unexpected as turning
            # the device on when its already on isn't expected to reset state.
            _LOGGER.debug(
                "%s: Current activity is already %s", self.name, activity_name
            )
            return

        await self.async_lock_start_activity()
        try:
            await self._client.start_activity(activity_id)
        except aioexc.TimeOut:
            _LOGGER.error("%s: Starting activity %s timed-out", self.name, activity)
            self.async_unlock_start_activity()