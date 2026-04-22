def test_query_string_and_page_script_hash_saved(self):
        scriptrunner = TestScriptRunner("good_script.py")
        scriptrunner.request_rerun(
            RerunData(query_string="foo=bar", page_script_hash="hash1")
        )
        scriptrunner.start()
        scriptrunner.join()

        self._assert_no_exceptions(scriptrunner)
        self._assert_events(
            scriptrunner,
            [
                ScriptRunnerEvent.SCRIPT_STARTED,
                ScriptRunnerEvent.ENQUEUE_FORWARD_MSG,
                ScriptRunnerEvent.SCRIPT_STOPPED_WITH_SUCCESS,
                ScriptRunnerEvent.SHUTDOWN,
            ],
        )

        shutdown_data = scriptrunner.event_data[-1]
        self.assertEqual(shutdown_data["client_state"].query_string, "foo=bar")
        self.assertEqual(shutdown_data["client_state"].page_script_hash, "hash1")