def test_basic_syntax06(self):
        """
        A variable may not contain more than one word
        """
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("basic-syntax06")