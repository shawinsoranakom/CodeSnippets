def _assert_no_exceptions(self, scriptrunner: "TestScriptRunner") -> None:
        """Assert that no uncaught exceptions were thrown in the
        scriptrunner's run thread.
        """
        self.assertEqual([], scriptrunner.script_thread_exceptions)