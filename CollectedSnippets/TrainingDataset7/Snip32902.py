def test_escape03(self):
        output = self.engine.render_to_string("escape03", {"a": "x&y"})
        self.assertEqual(output, "x&amp;y")