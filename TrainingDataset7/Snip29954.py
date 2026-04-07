def test_max(self):
        validator = RangeMaxValueValidator(5)
        validator(NumericRange(0, 5))
        msg = "Ensure that the upper bound of the range is not greater than 5."
        with self.assertRaises(exceptions.ValidationError) as cm:
            validator(NumericRange(0, 10))
        self.assertEqual(cm.exception.messages[0], msg)
        self.assertEqual(cm.exception.code, "max_value")
        with self.assertRaisesMessage(exceptions.ValidationError, msg):
            validator(NumericRange(0, None))