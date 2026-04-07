def test_inheritance39(self):
        output = self.engine.render_to_string("inheritance39", {"optional": True})
        self.assertEqual(output, "1new23")