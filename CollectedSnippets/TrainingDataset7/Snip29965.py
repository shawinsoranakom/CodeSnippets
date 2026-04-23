def test_integer_lower_bound_higher(self):
        field = pg_forms.IntegerRangeField()
        with self.assertRaises(exceptions.ValidationError) as cm:
            field.clean(["10", "2"])
        self.assertEqual(
            cm.exception.messages[0],
            "The start of the range must not exceed the end of the range.",
        )
        self.assertEqual(cm.exception.code, "bound_ordering")