async def async_scheduled_update_request(self, *_) -> None:
        """Request a state update from the blind at a scheduled point in time."""
        # add the last position to the list and keep the list at max 2 items
        self._previous_positions.append(self._blind.position)
        self._previous_angles.append(self._blind.angle)
        if len(self._previous_positions) > 2:
            del self._previous_positions[: len(self._previous_positions) - 2]
        if len(self._previous_angles) > 2:
            del self._previous_angles[: len(self._previous_angles) - 2]

        async with self._api_lock:
            await self.hass.async_add_executor_job(self._blind.Update_trigger)

        self.coordinator.async_update_listeners()

        if (
            len(self._previous_positions) < 2
            or not all(
                self._blind.position == prev_position
                for prev_position in self._previous_positions
            )
            or len(self._previous_angles) < 2
            or not all(
                self._blind.angle == prev_angle for prev_angle in self._previous_angles
            )
        ):
            # keep updating the position @self._update_interval_moving until the position does not change.
            self._requesting_position = async_call_later(
                self.hass,
                self._update_interval_moving,
                self.async_scheduled_update_request,
            )
        else:
            self._previous_positions = []
            self._previous_angles = []
            self._requesting_position = None