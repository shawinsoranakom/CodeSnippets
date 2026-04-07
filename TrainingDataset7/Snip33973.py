def test_spaceless06(self):
        output = self.engine.render_to_string("spaceless06", {"text": "This & that"})
        self.assertEqual(output, "<b><i>This & that</i></b>")