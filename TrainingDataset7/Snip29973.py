def test_decimal_incorrect_data_type(self):
        field = pg_forms.DecimalRangeField()
        with self.assertRaises(exceptions.ValidationError) as cm:
            field.clean("1.6")
        self.assertEqual(cm.exception.messages[0], "Enter two numbers.")
        self.assertEqual(cm.exception.code, "invalid")