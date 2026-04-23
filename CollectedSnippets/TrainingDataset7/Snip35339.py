def test_different_non_field_errors(self):
        msg = (
            "The non-field errors of form 0 of formset <TestFormset: bound=True "
            "valid=False total_forms=1> don't match."
        )
        with self.assertRaisesMessage(AssertionError, msg) as ctx:
            self.assertFormSetError(
                TestFormset.invalid(nonfield=True), 0, None, "other non-field error"
            )
        self.assertIn(
            "['non-field error'] != ['other non-field error']", str(ctx.exception)
        )
        msg_prefix = "Custom prefix"
        with self.assertRaisesMessage(AssertionError, f"{msg_prefix}: {msg}"):
            self.assertFormSetError(
                TestFormset.invalid(nonfield=True),
                0,
                None,
                "other non-field error",
                msg_prefix=msg_prefix,
            )