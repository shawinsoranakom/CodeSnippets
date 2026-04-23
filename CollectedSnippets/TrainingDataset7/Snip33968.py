def test_spaceless01(self):
        output = self.engine.render_to_string("spaceless01")
        self.assertEqual(output, "<b><i> text </i></b>")