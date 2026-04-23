def test_field_repr_nested(self):
        """__repr__() uses __qualname__ for nested class support."""
        self.assertEqual(repr(Nested.Field()), "<model_fields.tests.Nested.Field>")