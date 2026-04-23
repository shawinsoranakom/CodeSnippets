def test_cache11(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("cache11")