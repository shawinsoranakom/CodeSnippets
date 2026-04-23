def test_basic_syntax09(self):
        """
        Attribute syntax allows a template to call an object's attribute
        """
        output = self.engine.render_to_string("basic-syntax09", {"var": SomeClass()})
        self.assertEqual(output, "SomeClass.method")