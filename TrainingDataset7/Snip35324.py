def test_field_with_different_error(self):
        msg = (
            "The errors of field 'field' on form <TestForm bound=True, valid=False, "
            "fields=(field)> don't match."
        )
        with self.assertRaisesMessage(AssertionError, msg) as ctx:
            self.assertFormError(TestForm.invalid(), "field", "other error")
        self.assertIn("['invalid value'] != ['other error']", str(ctx.exception))
        msg_prefix = "Custom prefix"
        with self.assertRaisesMessage(AssertionError, f"{msg_prefix}: {msg}"):
            self.assertFormError(
                TestForm.invalid(), "field", "other error", msg_prefix=msg_prefix
            )