async def test_controller_detects_loop_and_produces_observation(
        self, mock_controller
    ):
        """Test that controller detects loops and produces LoopDetectionObservation."""
        # Setup stuck detector to detect a loop
        mock_controller._stuck_detector.is_stuck.return_value = True
        mock_controller._stuck_detector.stuck_analysis = MagicMock()
        mock_controller._stuck_detector.stuck_analysis.loop_type = (
            'repeating_action_observation'
        )
        mock_controller._stuck_detector.stuck_analysis.loop_start_idx = 5

        # Call attempt_loop_recovery
        result = mock_controller.attempt_loop_recovery()

        # Verify that loop recovery was attempted
        assert result is True

        # Verify that LoopDetectionObservation was added to event stream
        mock_controller.event_stream.add_event.assert_called()

        # Check that LoopDetectionObservation was created
        calls = mock_controller.event_stream.add_event.call_args_list
        loop_detection_found = False
        pause_action_found = False

        for call in calls:
            args, _ = call
            # add_event only takes one argument (the event)
            event = args[0]

            if isinstance(event, LoopDetectionObservation):
                loop_detection_found = True
                assert 'Agent detected in a loop!' in event.content
                assert 'repeating_action_observation' in event.content
                assert 'Loop detected at iteration 10' in event.content
            elif (
                hasattr(event, 'agent_state') and event.agent_state == AgentState.PAUSED
            ):
                pause_action_found = True

        assert loop_detection_found, 'LoopDetectionObservation should be created'
        assert pause_action_found, 'Agent should be paused'