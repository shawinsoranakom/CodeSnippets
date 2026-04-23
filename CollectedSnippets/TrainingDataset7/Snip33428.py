def test_basic_syntax23(self):
        """
        Treat "moo #} {{ cow" as the variable. Not ideal, but costly to work
        around, so this triggers an error.
        """
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("basic-syntax23")