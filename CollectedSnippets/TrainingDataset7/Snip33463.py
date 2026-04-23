def test_cache06(self):
        output = self.engine.render_to_string("cache06", {"foo": 2})
        self.assertEqual(output, "cache06")