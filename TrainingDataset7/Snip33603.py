def test_type_error_attribute(self):
        with self.assertRaises(TypeError):
            self.engine.render_to_string("template", {"var": SomeClass()})