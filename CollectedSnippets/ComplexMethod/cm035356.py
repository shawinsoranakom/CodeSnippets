def _is_stuck_context_window_error(
        self, filtered_history: list[Event], filtered_history_offset: int = 0
    ) -> bool:
        """Detects if we're stuck in a loop of context window errors.

        This happens when we repeatedly get context window errors and try to trim,
        but the trimming doesn't work, causing us to get more context window errors.
        The pattern is repeated AgentCondensationObservation events without any other
        events between them.

        Args:
            filtered_history: List of filtered events to check

        Returns:
            bool: True if we detect a context window error loop
        """
        # Look for AgentCondensationObservation events
        condensation_events = [
            (i, event)
            for i, event in enumerate(filtered_history)
            if isinstance(event, AgentCondensationObservation)
        ]

        # Need at least 10 condensation events to detect a loop
        if len(condensation_events) < 10:
            return False

        # Get the last 10 condensation events
        last_condensation_events = condensation_events[-10:]

        # Check if there are any non-condensation events between them
        for i in range(len(last_condensation_events) - 1):
            start_idx = last_condensation_events[i][0]
            end_idx = last_condensation_events[i + 1][0]

            # Look for any non-condensation events between these two
            has_other_events = False
            for event in filtered_history[start_idx + 1 : end_idx]:
                if not isinstance(event, AgentCondensationObservation):
                    has_other_events = True
                    break

            if not has_other_events:
                logger.warning(
                    'Context window error loop detected - repeated condensation events'
                )
                self.stuck_analysis = StuckDetector.StuckAnalysis(
                    loop_type='context_window_error',
                    loop_repeat_times=2,
                    loop_start_idx=start_idx + filtered_history_offset,
                )
                return True

        return False