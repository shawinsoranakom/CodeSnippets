def test_run_script_in_loop(self):
        """_run_script_thread should continue re-running its script
        while it has pending rerun requests."""
        scriptrunner = TestScriptRunner("not_a_script.py")

        # ScriptRequests.on_scriptrunner_ready will return 3 rerun requests,
        # and then stop.
        on_scriptrunner_ready_mock = MagicMock()
        on_scriptrunner_ready_mock.side_effect = [
            ScriptRequest(ScriptRequestType.RERUN, RerunData()),
            ScriptRequest(ScriptRequestType.RERUN, RerunData()),
            ScriptRequest(ScriptRequestType.RERUN, RerunData()),
            ScriptRequest(ScriptRequestType.STOP),
        ]

        scriptrunner._requests.on_scriptrunner_ready = on_scriptrunner_ready_mock

        run_script_mock = MagicMock()
        scriptrunner._run_script = run_script_mock

        scriptrunner.start()
        scriptrunner.join()

        # _run_script should have been called 3 times, once for each
        # RERUN request.
        self._assert_no_exceptions(scriptrunner)
        self.assertEqual(3, run_script_mock.call_count)