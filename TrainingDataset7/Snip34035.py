def test_url_fail18(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.render_to_string("url-fail18", {"named_url": "view"})