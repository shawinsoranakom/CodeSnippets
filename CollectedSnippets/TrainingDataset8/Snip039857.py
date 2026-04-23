def test_404_hash_not_found(self):
        scriptrunner = TestScriptRunner("good_script.py")
        scriptrunner.request_rerun(RerunData(page_script_hash="hash3"))
        scriptrunner.start()
        scriptrunner.join()

        self._assert_no_exceptions(scriptrunner)
        self._assert_events(
            scriptrunner,
            [
                ScriptRunnerEvent.SCRIPT_STARTED,
                ScriptRunnerEvent.ENQUEUE_FORWARD_MSG,  # page not found message
                ScriptRunnerEvent.ENQUEUE_FORWARD_MSG,  # deltas
                ScriptRunnerEvent.SCRIPT_STOPPED_WITH_SUCCESS,
                ScriptRunnerEvent.SHUTDOWN,
            ],
        )
        self._assert_text_deltas(scriptrunner, [text_utf])

        page_not_found_msg = scriptrunner.forward_msg_queue._queue[0].page_not_found
        self.assertEqual(page_not_found_msg.page_name, "")

        self.assertEqual(
            scriptrunner._main_script_path,
            sys.modules["__main__"].__file__,
            (" ScriptRunner should set the __main__.__file__" "attribute correctly"),
        )