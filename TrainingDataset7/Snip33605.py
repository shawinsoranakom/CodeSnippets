def test_filter02(self):
        output = self.engine.render_to_string("filter02")
        self.assertEqual(output, "DJANGO")