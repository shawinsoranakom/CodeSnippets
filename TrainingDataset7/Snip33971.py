def test_spaceless04(self):
        output = self.engine.render_to_string("spaceless04", {"text": "This & that"})
        self.assertEqual(output, "<b><i>This &amp; that</i></b>")