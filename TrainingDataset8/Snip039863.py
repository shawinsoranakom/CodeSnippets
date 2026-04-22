def _assert_num_deltas(
        self, scriptrunner: "TestScriptRunner", num_deltas: int
    ) -> None:
        """Assert that the given number of delta ForwardMsgs were enqueued
        during script execution.

        Parameters
        ----------
        scriptrunner : TestScriptRunner
        num_deltas : int

        """
        self.assertEqual(num_deltas, len(scriptrunner.deltas()))