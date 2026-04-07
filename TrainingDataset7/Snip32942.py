def test_force_escape02(self):
        output = self.engine.render_to_string("force-escape02", {"a": "x&y"})
        self.assertEqual(output, "x&amp;y")