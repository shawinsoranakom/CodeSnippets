def test_with_base_field_error_params(self):
        field = ArrayField(models.CharField(max_length=2))
        with self.assertRaises(exceptions.ValidationError) as cm:
            field.clean(["abc"], None)
        self.assertEqual(len(cm.exception.error_list), 1)
        exception = cm.exception.error_list[0]
        self.assertEqual(
            exception.message,
            "Item 1 in the array did not validate: Ensure this value has at most 2 "
            "characters (it has 3).",
        )
        self.assertEqual(exception.code, "item_invalid")
        self.assertEqual(
            exception.params,
            {"nth": 1, "value": "abc", "limit_value": 2, "show_value": 3},
        )