def test_no_non_field_errors(self):
        msg = (
            "The non-field errors of form 0 of formset <TestFormset: bound=True "
            "valid=False total_forms=1> don't match."
        )
        with self.assertRaisesMessage(AssertionError, msg) as ctx:
            self.assertFormSetError(TestFormset.invalid(), 0, None, "non-field error")
        self.assertIn("[] != ['non-field error']", str(ctx.exception))
        msg_prefix = "Custom prefix"
        with self.assertRaisesMessage(AssertionError, f"{msg_prefix}: {msg}"):
            self.assertFormSetError(
                TestFormset.invalid(), 0, None, "non-field error", msg_prefix=msg_prefix
            )