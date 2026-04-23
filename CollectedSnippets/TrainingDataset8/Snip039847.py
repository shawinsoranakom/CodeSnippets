def test_sessionstate_is_disconnected_after_stop(self):
        """After ScriptRunner.request_stop is called, any operations on its
        SessionState instance are no-ops.
        """
        # Create a TestRunner and stick some initial session_state into it.
        scriptrunner = TestScriptRunner("infinite_loop.py")
        scriptrunner._session_state["foo"] = "bar"
        self.assertEqual("bar", scriptrunner._session_state["foo"])
        scriptrunner.start()

        # Stop the TestRunner
        scriptrunner.request_stop()

        # We can neither get nor set SessionState values after request_stop.
        self.assertRaises(KeyError, lambda: scriptrunner._session_state["foo"])
        scriptrunner._session_state["new_foo"] = 3
        self.assertRaises(KeyError, lambda: scriptrunner._session_state["new_foo"])

        # Assert that Widget registration is a no-op
        widget_state = scriptrunner._session_state.register_widget(
            MagicMock(),
            user_key="mock_user_key",
        )
        self.assertEqual(False, widget_state.value_changed)

        # Ensure the ScriptRunner thread shuts down.
        scriptrunner.join()