def test_field_with_different_error(self):
        msg = (
            "The errors of field 'field' on form 0 of formset <TestFormset: bound=True "
            "valid=False total_forms=1> don't match."
        )
        with self.assertRaisesMessage(AssertionError, msg) as ctx:
            self.assertFormSetError(TestFormset.invalid(), 0, "field", "other error")
        self.assertIn("['invalid value'] != ['other error']", str(ctx.exception))
        msg_prefix = "Custom prefix"
        with self.assertRaisesMessage(AssertionError, f"{msg_prefix}: {msg}"):
            self.assertFormSetError(
                TestFormset.invalid(), 0, "field", "other error", msg_prefix=msg_prefix
            )