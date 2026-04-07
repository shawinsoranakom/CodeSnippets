def test_field_not_in_form(self):
        msg = (
            "The form <TestForm bound=True, valid=False, fields=(field)> does not "
            "contain the field 'other_field'."
        )
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertFormError(TestForm.invalid(), "other_field", "invalid value")
        msg_prefix = "Custom prefix"
        with self.assertRaisesMessage(AssertionError, f"{msg_prefix}: {msg}"):
            self.assertFormError(
                TestForm.invalid(),
                "other_field",
                "invalid value",
                msg_prefix=msg_prefix,
            )