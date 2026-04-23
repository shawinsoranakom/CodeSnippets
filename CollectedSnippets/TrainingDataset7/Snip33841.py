def test_invalidstr04(self):
        output = self.engine.render_to_string("invalidstr04")
        self.assertEqual(output, "No")