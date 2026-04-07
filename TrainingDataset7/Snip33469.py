def test_cache14(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.render_to_string("cache14", {"foo": "fail"})