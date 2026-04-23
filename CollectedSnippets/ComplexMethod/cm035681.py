def test_interactive_mode_resets_after_user_message(
        self, stuck_detector: StuckDetector
    ):
        state = stuck_detector.state

        # First add some actions that would be stuck in non-UI mode
        for i in range(4):
            cmd_action = CmdRunAction(command='ls')
            cmd_action._id = i
            state.history.append(cmd_action)
            cmd_observation = CmdOutputObservation(
                content='', command='ls', command_id=i
            )
            cmd_observation._cause = cmd_action._id
            state.history.append(cmd_observation)

        # In headless mode, this should be stuck
        assert stuck_detector.is_stuck(headless_mode=True) is True

        # with the UI, it will ALSO be stuck initially
        assert stuck_detector.is_stuck(headless_mode=False) is True

        # Add a user message
        message_action = MessageAction(content='Hello', wait_for_response=False)
        message_action._source = EventSource.USER
        state.history.append(message_action)

        # In not-headless mode, this should not be stuck because we ignore history before user message
        assert stuck_detector.is_stuck(headless_mode=False) is False

        # But in headless mode, this should be still stuck because user messages do not count
        assert stuck_detector.is_stuck(headless_mode=True) is True

        # Add two more identical actions - still not stuck because we need at least 3
        for i in range(2):
            cmd_action = CmdRunAction(command='ls')
            cmd_action._id = i + 4
            state.history.append(cmd_action)
            cmd_observation = CmdOutputObservation(
                content='', command='ls', command_id=i + 4
            )
            cmd_observation._cause = cmd_action._id
            state.history.append(cmd_observation)

        assert stuck_detector.is_stuck(headless_mode=False) is False

        # Add two more identical actions - now it should be stuck
        for i in range(2):
            cmd_action = CmdRunAction(command='ls')
            cmd_action._id = i + 6
            state.history.append(cmd_action)
            cmd_observation = CmdOutputObservation(
                content='', command='ls', command_id=i + 6
            )
            cmd_observation._cause = cmd_action._id
            state.history.append(cmd_observation)

        assert stuck_detector.is_stuck(headless_mode=False) is True