def test_calls_widget_callbacks(self, patched_call_callbacks):
        """Before a script is rerun, we call callbacks for any widgets
        whose value has changed.
        """
        scriptrunner = TestScriptRunner("widgets_script.py")
        scriptrunner.request_rerun(RerunData())
        scriptrunner.start()

        # Default widget values
        require_widgets_deltas([scriptrunner])
        self._assert_text_deltas(
            scriptrunner, ["False", "ahoy!", "0", "False", "loop_forever"]
        )

        patched_call_callbacks.assert_not_called()

        # Update widgets
        states = WidgetStates()
        w1_id = scriptrunner.get_widget_id("checkbox", "checkbox")
        _create_widget(w1_id, states).bool_value = True
        w2_id = scriptrunner.get_widget_id("text_area", "text_area")
        _create_widget(w2_id, states).string_value = "matey!"
        w3_id = scriptrunner.get_widget_id("radio", "radio")
        _create_widget(w3_id, states).int_value = 2
        w4_id = scriptrunner.get_widget_id("button", "button")
        _create_widget(w4_id, states).trigger_value = True

        # Explicitly clear deltas before re-running, to prevent a race
        # condition. (The ScriptRunner will clear the deltas when it
        # starts the re-run, but if that doesn't happen before
        # require_widgets_deltas() starts polling the ScriptRunner's deltas,
        # it will see stale deltas from the last run.)
        scriptrunner.clear_forward_msgs()
        scriptrunner.request_rerun(RerunData(widget_states=states))
        require_widgets_deltas([scriptrunner])

        patched_call_callbacks.assert_called_once()
        self._assert_text_deltas(
            scriptrunner, ["True", "matey!", "2", "True", "loop_forever"]
        )

        scriptrunner.request_stop()
        scriptrunner.join()