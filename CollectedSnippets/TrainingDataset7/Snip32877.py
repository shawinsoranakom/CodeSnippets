def test_default_if_none02(self):
        output = self.engine.render_to_string("default_if_none02", {"a": None})
        self.assertEqual(output, "x<")