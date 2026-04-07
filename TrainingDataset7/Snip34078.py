def test_with01(self):
        output = self.engine.render_to_string("with01", {"dict": {"key": 50}})
        self.assertEqual(output, "50")