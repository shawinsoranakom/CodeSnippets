def test_datetime_lower_bound_higher(self):
        field = pg_forms.DateTimeRangeField()
        with self.assertRaises(exceptions.ValidationError) as cm:
            field.clean(["2006-10-25 14:59", "2006-10-25 14:58"])
        self.assertEqual(
            cm.exception.messages[0],
            "The start of the range must not exceed the end of the range.",
        )
        self.assertEqual(cm.exception.code, "bound_ordering")