def test_spaceless03(self):
        output = self.engine.render_to_string("spaceless03")
        self.assertEqual(output, "<b><i>text</i></b>")