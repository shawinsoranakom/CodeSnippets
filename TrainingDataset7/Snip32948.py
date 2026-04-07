def test_force_escape08(self):
        output = self.engine.render_to_string("force-escape08", {"a": "x&y"})
        self.assertEqual(output, "x&amp;amp;y")