def test_is_stuck_repeating_action_observation(self, stuck_detector: StuckDetector):
        state = stuck_detector.state
        message_action = MessageAction(content='Done', wait_for_response=False)
        message_action._source = EventSource.USER

        hello_action = MessageAction(content='Hello', wait_for_response=False)
        hello_observation = NullObservation('')

        # 2 events
        state.history.append(hello_action)
        state.history.append(hello_observation)

        cmd_action_1 = CmdRunAction(command='ls')
        cmd_action_1._id = 1
        state.history.append(cmd_action_1)
        cmd_observation_1 = CmdOutputObservation(content='', command='ls')
        cmd_observation_1._cause = cmd_action_1._id
        state.history.append(cmd_observation_1)
        # 4 events

        cmd_action_2 = CmdRunAction(command='ls')
        cmd_action_2._id = 2
        state.history.append(cmd_action_2)
        cmd_observation_2 = CmdOutputObservation(content='', command='ls')
        cmd_observation_2._cause = cmd_action_2._id
        state.history.append(cmd_observation_2)
        # 6 events

        # random user message just because we can
        message_null_observation = NullObservation(content='')
        state.history.append(message_action)
        state.history.append(message_null_observation)
        # 8 events

        assert stuck_detector.is_stuck(headless_mode=True) is False

        cmd_action_3 = CmdRunAction(command='ls')
        cmd_action_3._id = 3
        state.history.append(cmd_action_3)
        cmd_observation_3 = CmdOutputObservation(content='', command='ls')
        cmd_observation_3._cause = cmd_action_3._id
        state.history.append(cmd_observation_3)
        # 10 events

        assert len(state.history) == 10
        assert stuck_detector.is_stuck(headless_mode=True) is False

        cmd_action_4 = CmdRunAction(command='ls')
        cmd_action_4._id = 4
        state.history.append(cmd_action_4)
        cmd_observation_4 = CmdOutputObservation(content='', command='ls')
        cmd_observation_4._cause = cmd_action_4._id
        state.history.append(cmd_observation_4)
        # 12 events

        assert len(state.history) == 12

        with patch('logging.Logger.warning') as mock_warning:
            assert stuck_detector.is_stuck(headless_mode=True) is True
            mock_warning.assert_called_once_with('Action, Observation loop detected')

        # recover to before first loop pattern
        assert stuck_detector.stuck_analysis.loop_type == 'repeating_action_observation'
        assert stuck_detector.stuck_analysis.loop_repeat_times == 4
        assert stuck_detector.stuck_analysis.loop_start_idx == 1