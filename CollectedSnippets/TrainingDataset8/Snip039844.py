def test_runtime_error(self, show_error_details: bool):
        """Tests that we correctly handle scripts with runtime errors."""
        with testutil.patch_config_options(
            {"client.showErrorDetails": show_error_details}
        ):
            scriptrunner = TestScriptRunner("runtime_error.py")
            scriptrunner.request_rerun(RerunData())
            scriptrunner.start()
            scriptrunner.join()

            self._assert_no_exceptions(scriptrunner)
            self._assert_events(
                scriptrunner,
                [
                    ScriptRunnerEvent.SCRIPT_STARTED,
                    ScriptRunnerEvent.ENQUEUE_FORWARD_MSG,  # text delta
                    ScriptRunnerEvent.ENQUEUE_FORWARD_MSG,  # exception delta
                    ScriptRunnerEvent.SCRIPT_STOPPED_WITH_SUCCESS,
                    ScriptRunnerEvent.SHUTDOWN,
                ],
            )

            # We'll get two deltas: one for st.text(), and one for the
            # exception that gets thrown afterwards.
            elts = scriptrunner.elements()
            self.assertEqual(elts[0].WhichOneof("type"), "text")

            if show_error_details:
                self._assert_num_deltas(scriptrunner, 2)
                self.assertEqual(elts[1].WhichOneof("type"), "exception")
            else:
                self._assert_num_deltas(scriptrunner, 2)
                self.assertEqual(elts[1].WhichOneof("type"), "exception")
                exc_msg = elts[1].exception.message
                self.assertTrue(_GENERIC_UNCAUGHT_EXCEPTION_TEXT == exc_msg)