def test_firstof10(self):
        output = self.engine.render_to_string("firstof10", {"a": "<"})
        self.assertEqual(output, "&lt;")