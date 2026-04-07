def test_filter05(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("filter05")