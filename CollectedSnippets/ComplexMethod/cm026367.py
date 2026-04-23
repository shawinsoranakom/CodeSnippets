async def async_update(
        self, event: Event[EventStateChangedData] | None
    ) -> HistoryStatsState:
        """Update the stats at a given time."""
        # Get previous values of start and end
        previous_period_start, previous_period_end = self._period
        # Parse templates
        self._period = async_calculate_period(
            self._duration, self._start, self._end, log_errors=not self._preview
        )
        # Get the current period
        current_period_start, current_period_end = self._period

        # Convert times to UTC
        current_period_start = dt_util.as_utc(current_period_start)
        current_period_end = dt_util.as_utc(current_period_end)
        previous_period_start = dt_util.as_utc(previous_period_start)
        previous_period_end = dt_util.as_utc(previous_period_end)

        # Compute integer timestamps
        current_period_start_timestamp = floored_timestamp(current_period_start)
        current_period_end_timestamp = floored_timestamp(current_period_end)
        previous_period_start_timestamp = floored_timestamp(previous_period_start)
        previous_period_end_timestamp = floored_timestamp(previous_period_end)
        utc_now = dt_util.utcnow()
        now_timestamp = floored_timestamp(utc_now)

        # If we end up querying data from the recorder when we get triggered by a new state
        # change event, it is possible this function could be reentered a second time before
        # the first recorder query returns. In that case a second recorder query will be done
        # and we need to hold the new event so that we can append it after the second query.
        # Otherwise the event will be dropped.
        if event:
            self._pending_events.append(event)

        if current_period_start_timestamp > now_timestamp:
            # History cannot tell the future
            self._history_current_period = []
            self._has_recorder_data = False
            self._state = HistoryStatsState(None, None, self._period)
            return self._state
        #
        # We avoid querying the database if the below did NOT happen:
        #
        # - No previous run occurred (uninitialized)
        # - The start time moved back in time
        # - The end time moved back in time
        # - The previous period ended before now
        #
        if (
            self._has_recorder_data
            and current_period_start_timestamp >= previous_period_start_timestamp
            and (
                current_period_end_timestamp == previous_period_end_timestamp
                or (
                    current_period_end_timestamp >= previous_period_end_timestamp
                    and previous_period_end_timestamp <= now_timestamp
                )
            )
        ):
            start_changed = (
                current_period_start_timestamp != previous_period_start_timestamp
            )
            end_changed = current_period_end_timestamp != previous_period_end_timestamp
            if start_changed:
                self._prune_history_cache(current_period_start_timestamp)

            new_data = False
            if event and (new_state := event.data["new_state"]) is not None:
                if current_period_start_timestamp <= floored_timestamp(
                    new_state.last_changed
                ):
                    self._history_current_period.append(
                        HistoryState(new_state.state, new_state.last_changed_timestamp)
                    )
                    new_data = True
            if (
                not new_data
                and current_period_end_timestamp < now_timestamp
                and not start_changed
                and not end_changed
            ):
                # If period has not changed and current time after the period end...
                # Don't compute anything as the value cannot have changed
                return self._state
        else:
            await self._async_history_from_db(
                current_period_start_timestamp, now_timestamp
            )
            for pending_event in self._pending_events:
                if (new_state := pending_event.data["new_state"]) is not None:
                    if current_period_start_timestamp <= floored_timestamp(
                        new_state.last_changed
                    ):
                        self._history_current_period.append(
                            HistoryState(
                                new_state.state, new_state.last_changed_timestamp
                            )
                        )

            self._has_recorder_data = True

        if self._query_count == 0:
            self._pending_events.clear()

        seconds_matched, match_count = self._async_compute_seconds_and_changes(
            now_timestamp,
            current_period_start_timestamp,
            current_period_end_timestamp,
        )
        self._state = HistoryStatsState(seconds_matched, match_count, self._period)
        return self._state