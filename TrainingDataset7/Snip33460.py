def test_cache03(self):
        output = self.engine.render_to_string("cache03")
        self.assertEqual(output, "cache03")