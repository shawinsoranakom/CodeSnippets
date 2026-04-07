def test_url_fail04(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("url-fail04")