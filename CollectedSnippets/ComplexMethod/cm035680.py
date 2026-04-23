async def test_controller_truncates_history_during_loop_recovery(
        self, mock_controller
    ):
        """Test that controller correctly truncates history during loop recovery."""
        # Setup mock history with events
        from openhands.events.action import CmdRunAction
        from openhands.events.observation import CmdOutputObservation, NullObservation

        # Create a realistic history with 10 events
        mock_history = []

        # Add initial user message
        user_msg = MessageAction(
            content='Hello, help me with this task', wait_for_response=False
        )
        user_msg._source = 'user'
        user_msg._id = 1
        mock_history.append(user_msg)

        # Add agent response
        agent_obs = NullObservation(content='')
        agent_obs._id = 2
        mock_history.append(agent_obs)

        # Add some commands and observations (simulating a loop)
        for i in range(3, 11):
            if i % 2 == 1:  # Action
                cmd = CmdRunAction(command='ls -la')
                cmd._id = i
                mock_history.append(cmd)
            else:  # Observation
                obs = CmdOutputObservation(
                    content='file1.txt file2.txt', command='ls -la'
                )
                obs._id = i
                obs._cause = i - 1
                mock_history.append(obs)

        # Set the mock history
        mock_controller.state.history = mock_history
        mock_controller.state.end_id = 10

        # Setup stuck analysis to indicate loop starts at index 5
        mock_controller._stuck_detector.stuck_analysis = MagicMock()
        mock_controller._stuck_detector.stuck_analysis.loop_start_idx = 5

        # Create LoopRecoveryAction with option 1 (truncate memory)
        LoopRecoveryAction(option=1)

        # Test actual truncation by calling the _perform_loop_recovery method directly
        # Reset history for actual truncation test
        mock_controller.state.history = mock_history.copy()
        mock_controller.state.end_id = 10

        # Call the actual _perform_loop_recovery method directly
        print(
            f'Before truncation: {len(mock_controller.state.history)} events, recovery_point={mock_controller._stuck_detector.stuck_analysis.loop_start_idx}'
        )
        print(
            f'_perform_loop_recovery method: {mock_controller._perform_loop_recovery}'
        )
        print(
            f'_truncate_memory_to_point method: {mock_controller._truncate_memory_to_point}'
        )
        await mock_controller._perform_loop_recovery(
            mock_controller._stuck_detector.stuck_analysis
        )

        # Debug: print the actual history after truncation
        print(f'History after truncation: {len(mock_controller.state.history)} events')
        for i, event in enumerate(mock_controller.state.history):
            print(f'  Event {i}: id={event.id}, type={type(event).__name__}')

        # Verify that history was truncated to the recovery point
        # The recovery point is index 5, so we should keep events 0-4 (5 events)
        assert len(mock_controller.state.history) == 5, (
            f'Expected 5 events after truncation, got {len(mock_controller.state.history)}'
        )

        # Verify the specific events that remain
        expected_ids = [1, 2, 3, 4, 5]
        for i, event in enumerate(mock_controller.state.history):
            assert event.id == expected_ids[i], (
                f'Event at index {i} should have id {expected_ids[i]}, got {event.id}'
            )

        # Verify end_id was updated
        assert mock_controller.state.end_id == 5, (
            f'Expected end_id to be 5, got {mock_controller.state.end_id}'
        )