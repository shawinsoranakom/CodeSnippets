def test_inheritance31(self):
        output = self.engine.render_to_string("inheritance31", {"optional": True})
        self.assertEqual(output, "1two3")