def test_include07(self):
        output = self.engine.render_to_string("include07", {"headline": "Included"})
        self.assertEqual(output, "Inline")