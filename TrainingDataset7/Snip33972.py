def test_spaceless05(self):
        output = self.engine.render_to_string("spaceless05", {"text": "This & that"})
        self.assertEqual(output, "<b><i>This & that</i></b>")