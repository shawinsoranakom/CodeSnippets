async def async_added_to_hass(self) -> None:
        """Register callbacks."""

        if "recorder" in self.hass.config.components:
            history_list = []
            largest_window_items = 0
            largest_window_time = timedelta(0)

            # Determine the largest window_size by type
            for filt in self._filters:
                if (
                    filt.window_unit == WINDOW_SIZE_UNIT_NUMBER_EVENTS
                    and largest_window_items < (size := cast(int, filt.window_size))
                ):
                    largest_window_items = size
                elif (
                    filt.window_unit == WINDOW_SIZE_UNIT_TIME
                    and largest_window_time < (val := cast(timedelta, filt.window_size))
                ):
                    largest_window_time = val

            # Retrieve the largest window_size of each type
            if largest_window_items > 0:
                filter_history = await get_instance(self.hass).async_add_executor_job(
                    partial(
                        history.get_last_state_changes,
                        self.hass,
                        largest_window_items,
                        entity_id=self._entity,
                    )
                )
                if self._entity in filter_history:
                    history_list.extend(filter_history[self._entity])
            if largest_window_time > timedelta(seconds=0):
                start = dt_util.utcnow() - largest_window_time
                filter_history = await get_instance(self.hass).async_add_executor_job(
                    partial(
                        history.state_changes_during_period,
                        self.hass,
                        start,
                        entity_id=self._entity,
                    )
                )
                if self._entity in filter_history:
                    history_list.extend(
                        [
                            state
                            for state in filter_history[self._entity]
                            if state not in history_list
                        ]
                    )

            # Sort the window states
            history_list = sorted(history_list, key=lambda s: s.last_updated)
            _LOGGER.debug(
                "Loading from history: %s",
                [(s.state, s.last_updated) for s in history_list],
            )

            # Replay history through the filter chain
            for state in history_list:
                if state.state not in [STATE_UNKNOWN, STATE_UNAVAILABLE, None]:
                    self._update_filter_sensor_state(state, False)

        @callback
        def _async_hass_started(hass: HomeAssistant) -> None:
            """Delay source entity tracking."""
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [self._entity], self._update_filter_sensor_state_event
                )
            )

        self.async_on_remove(async_at_started(self.hass, _async_hass_started))