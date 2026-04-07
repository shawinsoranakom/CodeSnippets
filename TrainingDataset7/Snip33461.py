def test_cache04(self):
        self.engine.render_to_string("cache03")
        output = self.engine.render_to_string("cache04")
        self.assertEqual(output, "cache03")