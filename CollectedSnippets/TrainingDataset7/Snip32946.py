def test_force_escape06(self):
        output = self.engine.render_to_string("force-escape06", {"a": "x&y"})
        self.assertEqual(output, "x&amp;y")