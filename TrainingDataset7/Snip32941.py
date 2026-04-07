def test_force_escape01(self):
        output = self.engine.render_to_string("force-escape01", {"a": "x&y"})
        self.assertEqual(output, "x&amp;y")