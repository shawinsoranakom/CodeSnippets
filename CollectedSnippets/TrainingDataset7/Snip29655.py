def test_validate_fail_base_field_error_params(self):
        field = SimpleArrayField(forms.CharField(max_length=2))
        with self.assertRaises(exceptions.ValidationError) as cm:
            field.clean("abc,c,defg")
        errors = cm.exception.error_list
        self.assertEqual(len(errors), 2)
        first_error = errors[0]
        self.assertEqual(
            first_error.message,
            "Item 1 in the array did not validate: Ensure this value has at most 2 "
            "characters (it has 3).",
        )
        self.assertEqual(first_error.code, "item_invalid")
        self.assertEqual(
            first_error.params,
            {"nth": 1, "value": "abc", "limit_value": 2, "show_value": 3},
        )
        second_error = errors[1]
        self.assertEqual(
            second_error.message,
            "Item 3 in the array did not validate: Ensure this value has at most 2 "
            "characters (it has 4).",
        )
        self.assertEqual(second_error.code, "item_invalid")
        self.assertEqual(
            second_error.params,
            {"nth": 3, "value": "defg", "limit_value": 2, "show_value": 4},
        )