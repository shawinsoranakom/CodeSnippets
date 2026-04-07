def test_load04(self):
        output = self.engine.render_to_string("load04")
        self.assertEqual(output, "this that theother and another thing")