def test_rerun_coalesce_none_and_none(self):
        """Coalesce two null-WidgetStates rerun requests."""
        reqs = ScriptRequests()

        # Request a rerun with null WidgetStates
        success = reqs.request_rerun(RerunData(widget_states=None))
        self.assertTrue(success)
        self.assertEqual(ScriptRequestType.RERUN, reqs._state)

        # Request another
        reqs.request_rerun(RerunData(widget_states=None))
        self.assertTrue(success)
        self.assertEqual(ScriptRequestType.RERUN, reqs._state)

        # The resulting RerunData should have null widget_states
        self.assertEqual(RerunData(widget_states=None), reqs._rerun_data)