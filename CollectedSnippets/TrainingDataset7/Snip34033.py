def test_url_fail16(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.render_to_string("url-fail16", {"named_url": "view"})