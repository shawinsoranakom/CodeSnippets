def test_ifchanged_param04(self):
        """
        Test a date+hour like construct, where the hour of the last day is
        the same but the date had changed, so print the hour anyway.
        """
        output = self.engine.render_to_string(
            "ifchanged-param04",
            {"days": [{"hours": [1, 2, 3], "day": 1}, {"hours": [3], "day": 2}]},
        )
        self.assertEqual(output, "112323")