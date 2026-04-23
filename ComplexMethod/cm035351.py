def is_stuck(self, headless_mode: bool = True) -> bool:
        """Checks if the agent is stuck in a loop.

        Args:
            headless_mode: Matches AgentController's headless_mode.
                          If True: Consider all history (automated/testing)
                          If False: Consider only history after last user message (interactive)

        Returns:
            bool: True if the agent is stuck in a loop, False otherwise.
        """
        filtered_history_offset = 0
        if not headless_mode:
            # In interactive mode, only look at history after the last user message
            last_user_msg_idx = -1
            for i, event in enumerate(reversed(self.state.history)):
                if (
                    isinstance(event, MessageAction)
                    and event.source == EventSource.USER
                ):
                    last_user_msg_idx = len(self.state.history) - i - 1
                    break
            filtered_history_offset = last_user_msg_idx + 1
            history_to_check = self.state.history[last_user_msg_idx + 1 :]
        else:
            # In headless mode, look at all history
            history_to_check = self.state.history

        # Filter out user messages and null events
        filtered_history = [
            event
            for event in history_to_check
            if not (
                # Filter works elegantly in both modes:
                # - In headless: actively filters out user messages from full history
                # - In non-headless: no-op since we already sliced after last user message
                (isinstance(event, MessageAction) and event.source == EventSource.USER)
                # there might be some NullAction or NullObservation in the history at least for now
                or isinstance(event, (NullAction, NullObservation))
            )
        ]

        # it takes 3 actions minimum to detect a loop, otherwise nothing to do here
        if len(filtered_history) < 3:
            return False

        # the first few scenarios detect 3 or 4 repeated steps
        # prepare the last 4 actions and observations, to check them out
        last_actions: list[Event] = []
        last_observations: list[Event] = []

        # retrieve the last four actions and observations starting from the end of history, wherever they are
        for event in reversed(filtered_history):
            if isinstance(event, Action) and len(last_actions) < 4:
                last_actions.append(event)
            elif isinstance(event, Observation) and len(last_observations) < 4:
                last_observations.append(event)

            if len(last_actions) == 4 and len(last_observations) == 4:
                break

        # scenario 1: same action, same observation
        if self._is_stuck_repeating_action_observation(
            last_actions, last_observations, filtered_history, filtered_history_offset
        ):
            return True

        # scenario 2: same action, errors
        if self._is_stuck_repeating_action_error(
            last_actions, last_observations, filtered_history, filtered_history_offset
        ):
            return True

        # scenario 3: monologue
        if self._is_stuck_monologue(filtered_history, filtered_history_offset):
            return True

        # scenario 4: action, observation pattern on the last six steps
        if len(filtered_history) >= 6:
            if self._is_stuck_action_observation_pattern(
                filtered_history, filtered_history_offset
            ):
                return True

        # scenario 5: context window error loop
        if len(filtered_history) >= 10:
            if self._is_stuck_context_window_error(
                filtered_history, filtered_history_offset
            ):
                return True

        # Empty stuck_analysis when not stuck
        self.stuck_analysis = None
        return False