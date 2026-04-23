def test_include02(self):
        output = self.engine.render_to_string("include02", {"headline": "Included"})
        self.assertEqual(output, "Included")