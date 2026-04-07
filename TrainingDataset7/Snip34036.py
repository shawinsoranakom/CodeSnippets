def test_url_fail19(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.render_to_string("url-fail19", {"named_url": "view"})