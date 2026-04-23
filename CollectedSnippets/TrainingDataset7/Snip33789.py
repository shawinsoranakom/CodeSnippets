def test_ifchanged_param05(self):
        """
        Logically the same as above, just written with explicit ifchanged
        for the day.
        """
        output = self.engine.render_to_string(
            "ifchanged-param05",
            {"days": [{"hours": [1, 2, 3], "day": 1}, {"hours": [3], "day": 2}]},
        )
        self.assertEqual(output, "112323")