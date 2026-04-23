def test_filter06(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("filter06")