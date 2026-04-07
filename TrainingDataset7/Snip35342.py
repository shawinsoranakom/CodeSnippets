def test_different_non_form_errors(self):
        msg = (
            "The non-form errors of formset <TestFormset: bound=True valid=False "
            "total_forms=0> don't match."
        )
        with self.assertRaisesMessage(AssertionError, msg) as ctx:
            self.assertFormSetError(
                TestFormset.invalid(nonform=True), None, None, "other error"
            )
        self.assertIn("['error'] != ['other error']", str(ctx.exception))
        msg_prefix = "Custom prefix"
        with self.assertRaisesMessage(AssertionError, f"{msg_prefix}: {msg}"):
            self.assertFormSetError(
                TestFormset.invalid(nonform=True),
                None,
                None,
                "other error",
                msg_prefix=msg_prefix,
            )