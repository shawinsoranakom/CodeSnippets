def test_time06(self):
        output = self.engine.render_to_string("time06", {"obj": "non-datetime-value"})
        self.assertEqual(output, "")