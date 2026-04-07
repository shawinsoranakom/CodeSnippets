def test_url_fail17(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.render_to_string("url-fail17", {"named_url": "view"})