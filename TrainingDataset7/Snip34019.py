def test_url_fail01(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("url-fail01")