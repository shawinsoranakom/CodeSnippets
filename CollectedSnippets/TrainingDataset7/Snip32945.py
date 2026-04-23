def test_force_escape05(self):
        output = self.engine.render_to_string("force-escape05", {"a": "x&y"})
        self.assertEqual(output, "x&amp;y")