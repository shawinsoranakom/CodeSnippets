async def test_controller_no_loop_recovery_when_not_stuck(self, mock_controller):
        """Test that controller doesn't attempt recovery when not stuck."""
        # Setup no stuck analysis
        mock_controller._stuck_detector.stuck_analysis = None

        # Reset the mock to ignore any previous calls (like system message)
        mock_controller.event_stream.add_event.reset_mock()

        # Call attempt_loop_recovery
        result = mock_controller.attempt_loop_recovery()

        # Verify that no recovery was attempted
        assert result is False

        # Verify that no loop recovery events were added to the stream
        # (Note: there might be other events, but no loop recovery specific ones)
        calls = mock_controller.event_stream.add_event.call_args_list
        loop_recovery_events = [
            call
            for call in calls
            if len(call[0]) > 0
            and (
                isinstance(call[0][0], LoopDetectionObservation)
                or (
                    hasattr(call[0][0], 'agent_state')
                    and call[0][0].agent_state == AgentState.PAUSED
                )
            )
        ]
        assert len(loop_recovery_events) == 0, (
            'No loop recovery events should be added when not stuck'
        )