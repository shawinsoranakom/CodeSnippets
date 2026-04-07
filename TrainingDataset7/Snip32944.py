def test_force_escape04(self):
        output = self.engine.render_to_string("force-escape04", {"a": "x&y"})
        self.assertEqual(output, "x&amp;amp;y")