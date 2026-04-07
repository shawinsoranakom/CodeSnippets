def test_escape04(self):
        output = self.engine.render_to_string("escape04", {"a": "x&y"})
        self.assertEqual(output, "x&amp;y")