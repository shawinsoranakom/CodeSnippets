def _assert_events(
        self, scriptrunner: "TestScriptRunner", expected_events: List[ScriptRunnerEvent]
    ) -> None:
        """Assert that the ScriptRunnerEvents emitted by a TestScriptRunner
        are what we expect."""
        self.assertEqual(expected_events, scriptrunner.events)