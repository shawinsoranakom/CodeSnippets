def test_cache05(self):
        output = self.engine.render_to_string("cache05", {"foo": 1})
        self.assertEqual(output, "cache05")