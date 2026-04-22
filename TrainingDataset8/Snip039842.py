def test_calls_widget_callbacks_error(
        self, patched_call_callbacks, patched_st_exception
    ):
        """If an exception is raised from a callback function,
        it should result in a call to `streamlit.exception`.
        """
        patched_call_callbacks.side_effect = RuntimeError("Random Error")

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

        scriptrunner.join()

        patched_call_callbacks.assert_called_once()

        self._assert_control_events(
            scriptrunner,
            [
                ScriptRunnerEvent.SCRIPT_STARTED,
                ScriptRunnerEvent.SCRIPT_STOPPED_FOR_RERUN,
                ScriptRunnerEvent.SCRIPT_STARTED,
                # We use the SCRIPT_STOPPED_WITH_SUCCESS event even if the
                # script runs into an error during execution. The user is
                # informed of the error by an `st.exception` box that we check
                # for below.
                ScriptRunnerEvent.SCRIPT_STOPPED_WITH_SUCCESS,
                ScriptRunnerEvent.SHUTDOWN,
            ],
        )

        patched_st_exception.assert_called_once()