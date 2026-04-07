def test_force_escape03(self):
        output = self.engine.render_to_string("force-escape03", {"a": "x&y"})
        self.assertEqual(output, "x&amp;amp;y")