def test_default_if_none01(self):
        output = self.engine.render_to_string("default_if_none01", {"a": None})
        self.assertEqual(output, "x<")