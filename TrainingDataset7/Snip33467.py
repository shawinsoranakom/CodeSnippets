def test_cache12(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("cache12")