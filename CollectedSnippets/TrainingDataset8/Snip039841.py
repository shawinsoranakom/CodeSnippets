def test_calls_widget_callbacks_on_new_scriptrunner_instance(
        self, patched_call_callbacks
    ):
        """A new ScriptRunner instance will call widget callbacks
        if widget values have changed. (This differs slightly from
        `test_calls_widget_callbacks`, which tests that an *already-running*
        ScriptRunner calls its callbacks on rerun).
        """
        # Create a ScriptRunner and run it once so we can grab its widgets.
        scriptrunner = TestScriptRunner("widgets_script.py")
        scriptrunner.request_rerun(RerunData())
        scriptrunner.start()
        require_widgets_deltas([scriptrunner])
        scriptrunner.request_stop()
        scriptrunner.join()

        patched_call_callbacks.assert_not_called()

        # Set our checkbox's value to True
        states = WidgetStates()
        checkbox_id = scriptrunner.get_widget_id("checkbox", "checkbox")
        _create_widget(checkbox_id, states).bool_value = True

        # Create a *new* ScriptRunner with our new RerunData. Our callbacks
        # should be called this time.
        scriptrunner = TestScriptRunner("widgets_script.py")
        scriptrunner.request_rerun(RerunData(widget_states=states))
        scriptrunner.start()
        require_widgets_deltas([scriptrunner])
        scriptrunner.request_stop()
        scriptrunner.join()

        patched_call_callbacks.assert_called_once()