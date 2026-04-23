def test_default01(self):
        output = self.engine.render_to_string("default01", {"a": ""})
        self.assertEqual(output, "x<")