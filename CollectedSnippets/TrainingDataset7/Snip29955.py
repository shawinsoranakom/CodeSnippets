def test_min(self):
        validator = RangeMinValueValidator(5)
        validator(NumericRange(10, 15))
        msg = "Ensure that the lower bound of the range is not less than 5."
        with self.assertRaises(exceptions.ValidationError) as cm:
            validator(NumericRange(0, 10))
        self.assertEqual(cm.exception.messages[0], msg)
        self.assertEqual(cm.exception.code, "min_value")
        with self.assertRaisesMessage(exceptions.ValidationError, msg):
            validator(NumericRange(None, 10))