def test_different_non_field_errors(self):
        msg = (
            "The non-field errors of form <TestForm bound=True, valid=False, "
            "fields=(field)> don't match."
        )
        with self.assertRaisesMessage(AssertionError, msg) as ctx:
            self.assertFormError(
                TestForm.invalid(nonfield=True), None, "other non-field error"
            )
        self.assertIn(
            "['non-field error'] != ['other non-field error']", str(ctx.exception)
        )
        msg_prefix = "Custom prefix"
        with self.assertRaisesMessage(AssertionError, f"{msg_prefix}: {msg}"):
            self.assertFormError(
                TestForm.invalid(nonfield=True),
                None,
                "other non-field error",
                msg_prefix=msg_prefix,
            )