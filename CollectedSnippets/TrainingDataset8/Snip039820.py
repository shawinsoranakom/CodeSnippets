def test_rerun_coalesce_widgets_and_widgets(self):
        """Coalesce two non-null-WidgetStates rerun requests."""
        reqs = ScriptRequests()

        # Request a rerun with non-null WidgetStates.
        states = WidgetStates()
        _create_widget("trigger", states).trigger_value = True
        _create_widget("int", states).int_value = 123
        success = reqs.request_rerun(RerunData(widget_states=states))
        self.assertTrue(success)

        # Request another rerun. It should get coalesced with the first one.
        states = WidgetStates()
        _create_widget("trigger", states).trigger_value = False
        _create_widget("int", states).int_value = 456

        success = reqs.request_rerun(RerunData(widget_states=states))
        self.assertTrue(success)
        self.assertEqual(ScriptRequestType.RERUN, reqs._state)

        result_states = reqs._rerun_data.widget_states

        # Coalesced triggers should be True if either the old *or*
        # new value was True
        self.assertEqual(True, _get_widget("trigger", result_states).trigger_value)

        # Other widgets should have their newest value
        self.assertEqual(456, _get_widget("int", result_states).int_value)