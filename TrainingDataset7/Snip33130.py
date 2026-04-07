def test_aware_naive_type_error(self):
        output = self.engine.render_to_string(
            "timeuntil16", {"a": self.now_tz_i, "b": self.now}
        )
        self.assertEqual(output, "")