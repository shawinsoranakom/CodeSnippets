def test_firstof09(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("firstof09")