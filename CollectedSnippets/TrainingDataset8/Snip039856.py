def test_page_script_hash_to_script_path(self):
        scriptrunner = TestScriptRunner("good_script.py")
        scriptrunner.request_rerun(RerunData(page_name="good_script2"))
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
        self._assert_text_deltas(scriptrunner, [text_utf2])
        self.assertEqual(
            os.path.join(os.path.dirname(__file__), "test_data", "good_script2.py"),
            sys.modules["__main__"].__file__,
            (" ScriptRunner should set the __main__.__file__" "attribute correctly"),
        )

        shutdown_data = scriptrunner.event_data[-1]
        self.assertEqual(shutdown_data["client_state"].page_script_hash, "hash2")