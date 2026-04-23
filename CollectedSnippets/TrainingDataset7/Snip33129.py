def test_naive_aware_type_error(self):
        output = self.engine.render_to_string(
            "timeuntil15", {"a": self.now, "b": self.now_tz_i}
        )
        self.assertEqual(output, "")