def _is_stuck_action_observation_pattern(
        self, filtered_history: list[Event], filtered_history_offset: int = 0
    ) -> bool:
        # scenario 4: action, observation pattern on the last six steps
        # check if the agent repeats the same (Action, Observation)
        # every other step in the last six steps
        last_six_actions: list[Event] = []
        last_six_observations: list[Event] = []

        # the end of history is most interesting
        for event in reversed(filtered_history):
            if isinstance(event, Action) and len(last_six_actions) < 6:
                last_six_actions.append(event)
            elif isinstance(event, Observation) and len(last_six_observations) < 6:
                last_six_observations.append(event)

            if len(last_six_actions) == 6 and len(last_six_observations) == 6:
                break

        # this pattern is every other step, like:
        # (action_1, obs_1), (action_2, obs_2), (action_1, obs_1), (action_2, obs_2),...
        if len(last_six_actions) == 6 and len(last_six_observations) == 6:
            actions_equal = (
                # action_0 == action_2 == action_4
                self._eq_no_pid(last_six_actions[0], last_six_actions[2])
                and self._eq_no_pid(last_six_actions[0], last_six_actions[4])
                # action_1 == action_3 == action_5
                and self._eq_no_pid(last_six_actions[1], last_six_actions[3])
                and self._eq_no_pid(last_six_actions[1], last_six_actions[5])
            )
            observations_equal = (
                # obs_0 == obs_2 == obs_4
                self._eq_no_pid(last_six_observations[0], last_six_observations[2])
                and self._eq_no_pid(last_six_observations[0], last_six_observations[4])
                # obs_1 == obs_3 == obs_5
                and self._eq_no_pid(last_six_observations[1], last_six_observations[3])
                and self._eq_no_pid(last_six_observations[1], last_six_observations[5])
            )

            if actions_equal and observations_equal:
                logger.warning('Action, Observation pattern detected')
                self.stuck_analysis = StuckDetector.StuckAnalysis(
                    loop_type='repeating_action_observation_pattern',
                    loop_repeat_times=3,
                    loop_start_idx=filtered_history.index(last_six_actions[-1])
                    + filtered_history_offset,
                )
                return True
        return False