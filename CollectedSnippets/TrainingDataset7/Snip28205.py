def test_deconstruct_nested_field(self):
        """deconstruct() uses __qualname__ for nested class support."""
        name, path, args, kwargs = Nested.Field().deconstruct()
        self.assertEqual(path, "model_fields.tests.Nested.Field")