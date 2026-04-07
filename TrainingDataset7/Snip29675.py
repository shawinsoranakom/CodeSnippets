def test_invalid_integer(self):
        msg = (
            "Item 2 in the array did not validate: Ensure this value is less than or "
            "equal to 100."
        )
        with self.assertRaisesMessage(exceptions.ValidationError, msg):
            SplitArrayField(forms.IntegerField(max_value=100), size=2).clean([0, 101])