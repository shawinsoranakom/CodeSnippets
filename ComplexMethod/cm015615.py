def test_start_supports_sigusr1_and_sigusr2(
        self, mock_logger, mock_signal, mock_threading
    ):
        """Test that the start method properly supports SIGUSR1 and SIGUSR2 signals."""
        # Setup
        mock_threading.current_thread.return_value = (
            mock_threading.main_thread.return_value
        )
        mock_pcontext = MagicMock(spec=PContext)
        # Mock the stdout_tail and stderr_tail
        mock_stdout_tail = MagicMock()
        mock_stderr_tail = MagicMock()
        mock_pcontext._tail_logs = [mock_stdout_tail, mock_stderr_tail]

        # Set environment variable to include SIGUSR1 and SIGUSR2
        os.environ["TORCHELASTIC_SIGNALS_TO_HANDLE"] = "SIGUSR1,SIGUSR2"

        # Mock signal attributes to have SIGUSR1 and SIGUSR2
        mock_signal.SIGUSR1 = signal.SIGUSR1
        mock_signal.SIGUSR2 = signal.SIGUSR2

        # Call the start method
        PContext.start(mock_pcontext)

        # Verify that signal.signal was called for both SIGUSR1 and SIGUSR2
        signal_calls = mock_signal.signal.call_args_list
        registered_signals = [
            call[0][0] for call in signal_calls
        ]  # Extract the signal from each call

        # Verify both SIGUSR1 and SIGUSR2 were registered
        self.assertIn(
            signal.SIGUSR1, registered_signals, "SIGUSR1 should be registered"
        )
        self.assertIn(
            signal.SIGUSR2, registered_signals, "SIGUSR2 should be registered"
        )

        # Verify the correct handler was registered for both signals
        for call in signal_calls:
            sig, handler = call[0]
            if sig in [signal.SIGUSR1, signal.SIGUSR2]:
                self.assertEqual(
                    handler,
                    _terminate_process_handler,
                    f"Signal {sig} should use _terminate_process_handler",
                )

        # Verify that info messages were logged for successful registration
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        sigusr1_logged = any(
            "SIGUSR1" in call and "Registered signal handler" in call
            for call in info_calls
        )
        sigusr2_logged = any(
            "SIGUSR2" in call and "Registered signal handler" in call
            for call in info_calls
        )

        self.assertTrue(
            sigusr1_logged,
            f"Expected SIGUSR1 registration message in info calls: {info_calls}",
        )
        self.assertTrue(
            sigusr2_logged,
            f"Expected SIGUSR2 registration message in info calls: {info_calls}",
        )

        # Verify _start was called
        mock_pcontext._start.assert_called_once()
        # Verify _stdout_tail.start() and _stderr_tail.start() were called
        mock_stdout_tail.start.assert_called_once()
        mock_stderr_tail.start.assert_called_once()