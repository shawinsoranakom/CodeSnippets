def test_spaceless02(self):
        output = self.engine.render_to_string("spaceless02")
        self.assertEqual(output, "<b><i> text </i></b>")