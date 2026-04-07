def test_field_not_in_form(self):
        msg = (
            "The form 0 of formset <TestFormset: bound=True valid=False total_forms=1> "
            "does not contain the field 'other_field'."
        )
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertFormSetError(
                TestFormset.invalid(), 0, "other_field", "invalid value"
            )
        msg_prefix = "Custom prefix"
        with self.assertRaisesMessage(AssertionError, f"{msg_prefix}: {msg}"):
            self.assertFormSetError(
                TestFormset.invalid(),
                0,
                "other_field",
                "invalid value",
                msg_prefix=msg_prefix,
            )