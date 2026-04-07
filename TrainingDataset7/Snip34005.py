def test_url05(self):
        output = self.engine.render_to_string("url05", {"v": "Ω"})
        self.assertEqual(output, "/%D0%AE%D0%BD%D0%B8%D0%BA%D0%BE%D0%B4/%CE%A9/")