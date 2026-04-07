def test_basic_syntax20b(self):
        """
        Don't silence a TypeError if it was raised inside a callable.
        """
        template = self.engine.get_template("basic-syntax20b")

        with self.assertRaises(TypeError):
            template.render(Context({"var": SomeClass()}))