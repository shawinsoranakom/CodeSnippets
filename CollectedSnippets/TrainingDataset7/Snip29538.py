def test_array_field(self):
        field = IntegerArrayModel._meta.get_field("field")
        self.assert_model_check_errors(
            IntegerArrayModel,
            [self._make_error(field, "ArrayField")],
        )