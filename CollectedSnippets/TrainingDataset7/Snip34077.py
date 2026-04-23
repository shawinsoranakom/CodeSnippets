def test_typeerror_as_var(self):
        output = self.engine.render_to_string("t", {"a": "a", "c": 100, "b": 100})
        self.assertEqual(output, "--")