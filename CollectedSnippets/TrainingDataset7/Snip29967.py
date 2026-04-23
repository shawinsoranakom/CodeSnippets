def test_integer_incorrect_data_type(self):
        field = pg_forms.IntegerRangeField()
        with self.assertRaises(exceptions.ValidationError) as cm:
            field.clean("1")
        self.assertEqual(cm.exception.messages[0], "Enter two whole numbers.")
        self.assertEqual(cm.exception.code, "invalid")