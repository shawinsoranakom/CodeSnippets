def test_default02(self):
        output = self.engine.render_to_string("default02", {"a": ""})
        self.assertEqual(output, "x<")