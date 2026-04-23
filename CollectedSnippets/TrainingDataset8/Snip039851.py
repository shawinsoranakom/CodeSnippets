def test_remove_nonexistent_elements(self):
        """Tests that nonexistent elements are removed from widget cache after script run."""

        widget_id = "nonexistent_widget_id"

        # Run script, sending in a WidgetStates containing our fake widget ID.
        scriptrunner = TestScriptRunner("good_script.py")
        states = WidgetStates()
        _create_widget(widget_id, states).string_value = "streamlit"
        scriptrunner.request_rerun(RerunData(widget_states=states))
        scriptrunner.start()

        # At this point, scriptrunner should have finished running, detected
        # that our widget_id wasn't in the list of widgets found this run, and
        # culled it. Ensure widget cache no longer holds our widget ID.
        self.assertRaises(KeyError, lambda: scriptrunner._session_state[widget_id])