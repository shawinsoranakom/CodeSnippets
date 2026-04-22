def test_maybe_handle_execution_control_request(self):
        """maybe_handle_execution_control_request should no-op if called
        from another thread.
        """
        runner = TestScriptRunner("not_a_script.py")
        runner._execing = True

        # Mock ScriptRequests.on_scriptrunner_yield(). It will return a fake
        # rerun request.
        requests_mock = MagicMock()
        requests_mock.on_scriptrunner_yield = MagicMock(
            return_value=ScriptRequest(ScriptRequestType.RERUN, RerunData())
        )
        runner._requests = requests_mock

        # If _is_in_script_thread is False, our request shouldn't get popped
        runner._is_in_script_thread = MagicMock(return_value=False)
        runner._maybe_handle_execution_control_request()
        requests_mock.on_scriptrunner_yield.assert_not_called()

        # If _is_in_script_thread is True, our rerun request should get
        # popped (and this will result in a RerunException being raised).
        runner._is_in_script_thread = MagicMock(return_value=True)
        with self.assertRaises(RerunException):
            runner._maybe_handle_execution_control_request()
        requests_mock.on_scriptrunner_yield.assert_called_once()