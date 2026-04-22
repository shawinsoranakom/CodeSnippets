def _assert_text_deltas(
        self, scriptrunner: "TestScriptRunner", text_deltas: List[str]
    ) -> None:
        """Assert that the scriptrunner's ForwardMsgQueue contains text deltas
        with the given contents.
        """
        self.assertEqual(text_deltas, scriptrunner.text_deltas())