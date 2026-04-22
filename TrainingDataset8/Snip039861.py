def _assert_control_events(
        self, scriptrunner: "TestScriptRunner", expected_events: List[ScriptRunnerEvent]
    ) -> None:
        """Assert the non-data ScriptRunnerEvents emitted by a TestScriptRunner
        are what we expect. ("Non-data" refers to all events except
        ENQUEUE_FORWARD_MSG.)
        """
        control_events = [
            event for event in scriptrunner.events if _is_control_event(event)
        ]
        self.assertEqual(expected_events, control_events)