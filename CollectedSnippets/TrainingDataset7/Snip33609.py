def test_filter05bis(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("filter05bis")