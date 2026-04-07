def test_url_fail07(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("url-fail07")