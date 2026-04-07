def test_inheritance40(self):
        output = self.engine.render_to_string("inheritance40", {"optional": 1})
        self.assertEqual(output, "1new23")