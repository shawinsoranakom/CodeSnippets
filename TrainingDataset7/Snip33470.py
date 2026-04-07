def test_cache15(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.render_to_string("cache15", {"foo": []})