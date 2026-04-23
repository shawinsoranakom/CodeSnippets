def test_shutdown(self):
        """Test that we can shutdown while a script is running."""
        scriptrunner = TestScriptRunner("infinite_loop.py")
        scriptrunner.request_rerun(RerunData())
        scriptrunner.start()

        time.sleep(0.1)
        scriptrunner.request_stop()
        scriptrunner.join()

        self._assert_no_exceptions(scriptrunner)
        self._assert_control_events(
            scriptrunner,
            [
                ScriptRunnerEvent.SCRIPT_STARTED,
                ScriptRunnerEvent.SCRIPT_STOPPED_WITH_SUCCESS,
                ScriptRunnerEvent.SHUTDOWN,
            ],
        )
        self._assert_text_deltas(scriptrunner, ["loop_forever"])