def test_cache07(self):
        context = {"foo": 1}
        self.engine.render_to_string("cache05", context)
        output = self.engine.render_to_string("cache07", context)
        self.assertEqual(output, "cache05")