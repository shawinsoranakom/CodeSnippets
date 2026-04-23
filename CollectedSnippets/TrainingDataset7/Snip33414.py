def test_basic_syntax10(self):
        """
        Multiple levels of attribute access are allowed.
        """
        output = self.engine.render_to_string("basic-syntax10", {"var": SomeClass()})
        self.assertEqual(output, "OtherClass.method")