def test_widgets(self):
        """Tests that widget values behave as expected."""
        scriptrunner = TestScriptRunner("widgets_script.py")
        scriptrunner.request_rerun(RerunData())
        scriptrunner.start()

        # Default widget values
        require_widgets_deltas([scriptrunner])
        self._assert_text_deltas(
            scriptrunner, ["False", "ahoy!", "0", "False", "loop_forever"]
        )

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
        self._assert_text_deltas(
            scriptrunner, ["True", "matey!", "2", "True", "loop_forever"]
        )

        # Rerun with previous values. Our button should be reset;
        # everything else should be the same.
        scriptrunner.clear_forward_msgs()
        scriptrunner.request_rerun(RerunData())

        require_widgets_deltas([scriptrunner])
        self._assert_text_deltas(
            scriptrunner, ["True", "matey!", "2", "False", "loop_forever"]
        )

        scriptrunner.request_stop()
        scriptrunner.join()
        self._assert_no_exceptions(scriptrunner)