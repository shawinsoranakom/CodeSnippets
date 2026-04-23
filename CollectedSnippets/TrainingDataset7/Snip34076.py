def test_zerodivisionerror_as_var(self):
        output = self.engine.render_to_string("t", {"a": 0, "b": 0})
        self.assertEqual(output, "-0-")