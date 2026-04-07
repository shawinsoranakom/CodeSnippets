def test_datetime_incorrect_data_type(self):
        field = pg_forms.DateTimeRangeField()
        with self.assertRaises(exceptions.ValidationError) as cm:
            field.clean("2013-04-09 11:45")
        self.assertEqual(cm.exception.messages[0], "Enter two valid date/times.")
        self.assertEqual(cm.exception.code, "invalid")