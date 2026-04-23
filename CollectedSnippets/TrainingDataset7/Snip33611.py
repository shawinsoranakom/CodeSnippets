def test_filter06bis(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("filter06bis")