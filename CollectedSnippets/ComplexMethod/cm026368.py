def _async_compute_seconds_and_changes(
        self, now_timestamp: float, start_timestamp: float, end_timestamp: float
    ) -> tuple[float, int]:
        """Compute the seconds matched and changes from the history list and first state."""
        # state_changes_during_period is called with include_start_time_state=True
        # which is the default and always provides the state at the start
        # of the period
        previous_state_matches = False
        last_state_change_timestamp = 0.0
        elapsed = 0.0
        match_count = 0

        # Make calculations
        for history_state in self._history_current_period:
            current_state_matches = history_state.state in self._entity_states
            state_change_timestamp = history_state.last_changed

            if math.floor(state_change_timestamp) > end_timestamp:
                break

            if math.floor(state_change_timestamp) > now_timestamp:
                # Shouldn't count states that are in the future
                _LOGGER.debug(
                    "Skipping future timestamp %s (now %s)",
                    state_change_timestamp,
                    now_timestamp,
                )
                break

            if not previous_state_matches and current_state_matches:
                # We are entering a matching state.
                # This marks the start of a new candidate block that may later
                # qualify if it lasts at least min_state_duration.
                last_state_change_timestamp = max(
                    start_timestamp, state_change_timestamp
                )
            elif previous_state_matches and not current_state_matches:
                # We are leaving a matching state.
                # This closes the current matching block and allows to
                # evaluate its total duration.
                block_duration = state_change_timestamp - last_state_change_timestamp
                if block_duration >= self._min_state_duration:
                    # The block lasted long enough so we increment match count
                    # and accumulate its duration.
                    elapsed += block_duration
                    match_count += 1

            previous_state_matches = current_state_matches

        # Count time elapsed between last history state and end of measure
        if previous_state_matches:
            # We are still inside a matching block at the end of the
            # measurement window. This block has not been closed by a
            # transition, so we evaluate it up to measure_end.
            measure_end = min(end_timestamp, now_timestamp)
            last_state_duration = max(0, measure_end - last_state_change_timestamp)
            if last_state_duration >= self._min_state_duration:
                # The open block lasted long enough so we increment match count
                # and accumulate its duration.
                elapsed += last_state_duration
                match_count += 1

        # Save value in seconds
        seconds_matched = elapsed
        return seconds_matched, match_count