def test_url_fail06(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("url-fail06")