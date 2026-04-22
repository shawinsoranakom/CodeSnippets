def test_rerun_coalesce_none_and_widgets(self):
        """Coalesce a null-WidgetStates rerun request with a
        non-null-WidgetStates request.
        """
        reqs = ScriptRequests()

        # Request a rerun with null WidgetStates.
        success = reqs.request_rerun(RerunData(widget_states=None))
        self.assertTrue(success)

        # Request a rerun with non-null WidgetStates.
        states = WidgetStates()
        _create_widget("trigger", states).trigger_value = True
        _create_widget("int", states).int_value = 123
        success = reqs.request_rerun(RerunData(widget_states=states))
        self.assertTrue(success)

        # The null WidgetStates request will be overwritten.
        result_states = reqs._rerun_data.widget_states
        self.assertEqual(True, _get_widget("trigger", result_states).trigger_value)
        self.assertEqual(123, _get_widget("int", result_states).int_value)