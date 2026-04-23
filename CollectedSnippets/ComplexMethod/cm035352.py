def _is_stuck_repeating_action_error(
        self,
        last_actions: list[Event],
        last_observations: list[Event],
        filtered_history: list[Event],
        filtered_history_offset: int = 0,
    ) -> bool:
        # scenario 2: same action, errors
        # it takes 3 actions and 3 observations to detect a loop
        # check if the last three actions are the same and result in errors

        if len(last_actions) < 3 or len(last_observations) < 3:
            return False

        # are the last three actions the "same"?
        if all(self._eq_no_pid(last_actions[0], action) for action in last_actions[:3]):
            # and the last three observations are all errors?
            if all(isinstance(obs, ErrorObservation) for obs in last_observations[:3]):
                logger.warning('Action, ErrorObservation loop detected')
                self.stuck_analysis = StuckDetector.StuckAnalysis(
                    loop_type='repeating_action_error',
                    loop_repeat_times=3,
                    loop_start_idx=filtered_history.index(last_actions[-1])
                    + filtered_history_offset,
                )
                return True
            # or, are the last three observations all IPythonRunCellObservation with SyntaxError?
            elif all(
                isinstance(obs, IPythonRunCellObservation)
                for obs in last_observations[:3]
            ):
                warning = 'Action, IPythonRunCellObservation loop detected'
                for error_message in self.SYNTAX_ERROR_MESSAGES:
                    if error_message.startswith(
                        'SyntaxError: unterminated string literal (detected at line'
                    ):
                        if self._check_for_consistent_line_error(
                            [
                                obs
                                for obs in last_observations[:3]
                                if isinstance(obs, IPythonRunCellObservation)
                            ],
                            error_message,
                        ):
                            logger.warning(warning)
                            self.stuck_analysis = StuckDetector.StuckAnalysis(
                                loop_type='repeating_action_error',
                                loop_repeat_times=3,
                                loop_start_idx=filtered_history.index(last_actions[-1])
                                + filtered_history_offset,
                            )
                            return True
                    elif error_message in (
                        'SyntaxError: invalid syntax. Perhaps you forgot a comma?',
                        'SyntaxError: incomplete input',
                    ) and self._check_for_consistent_invalid_syntax(
                        [
                            obs
                            for obs in last_observations[:3]
                            if isinstance(obs, IPythonRunCellObservation)
                        ],
                        error_message,
                    ):
                        logger.warning(warning)
                        self.stuck_analysis = StuckDetector.StuckAnalysis(
                            loop_type='repeating_action_error',
                            loop_repeat_times=3,
                            loop_start_idx=filtered_history.index(last_actions[-1])
                            + filtered_history_offset,
                        )
                        return True
        return False