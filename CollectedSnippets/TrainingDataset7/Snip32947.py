def test_force_escape07(self):
        output = self.engine.render_to_string("force-escape07", {"a": "x&y"})
        self.assertEqual(output, "x&amp;amp;y")