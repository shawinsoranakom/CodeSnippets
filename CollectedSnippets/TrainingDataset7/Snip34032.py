def test_url_fail15(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.render_to_string("url-fail15", {"named_url": "view"})