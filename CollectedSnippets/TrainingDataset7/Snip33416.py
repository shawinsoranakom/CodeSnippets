def test_basic_syntax12(self):
        """
        Raise TemplateSyntaxError when trying to access a variable
        beginning with an underscore.
        """
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("basic-syntax12")