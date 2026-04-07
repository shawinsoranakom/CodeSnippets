def test_nested_array_field(self):
        """Inner ArrayField does not cause a postgres.E001 error."""
        field = NestedIntegerArrayModel._meta.get_field("field")
        self.assert_model_check_errors(
            NestedIntegerArrayModel,
            [
                self._make_error(field, "ArrayField"),
            ],
        )