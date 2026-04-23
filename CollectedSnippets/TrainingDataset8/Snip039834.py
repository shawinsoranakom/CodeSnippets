def test_yield_on_enqueue(self, _, install_tracer: bool):
        """Make sure we try to handle execution control requests whenever
        our _enqueue_forward_msg function is called, unless "runner.installTracer" is set.
        """
        with testutil.patch_config_options({"runner.installTracer": install_tracer}):
            # Create a TestScriptRunner. We won't actually be starting its
            # script thread - instead, we'll manually call _enqueue_forward_msg on it, and
            # pretend we're in the script thread.
            runner = TestScriptRunner("not_a_script.py")
            runner._is_in_script_thread = MagicMock(return_value=True)

            # Mock the call to _maybe_handle_execution_control_request.
            # This is what we're testing gets called or not.
            maybe_handle_execution_control_request_mock = MagicMock()
            runner._maybe_handle_execution_control_request = (
                maybe_handle_execution_control_request_mock
            )

            # Enqueue a ForwardMsg on the runner
            mock_msg = MagicMock()
            runner._enqueue_forward_msg(mock_msg)

            # Ensure the ForwardMsg was delivered to event listeners.
            self._assert_forward_msgs(runner, [mock_msg])

            # If "install_tracer" is true, maybe_handle_execution_control_request
            # should not be called by the enqueue function. (In reality, it will
            # still be called once in the tracing callback But in this test
            # we're not actually installing a tracer - the script is not being
            # run.) If "install_tracer" is false, the function should be called
            # once.
            expected_call_count = 0 if install_tracer else 1
            self.assertEqual(
                expected_call_count,
                maybe_handle_execution_control_request_mock.call_count,
            )