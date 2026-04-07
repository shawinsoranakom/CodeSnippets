def test_unbound_form(self):
        msg = (
            "The form <TestForm bound=False, valid=Unknown, fields=(field)> is not "
            "bound, it will never have any errors."
        )
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertFormError(TestForm(), "field", [])
        msg_prefix = "Custom prefix"
        with self.assertRaisesMessage(AssertionError, f"{msg_prefix}: {msg}"):
            self.assertFormError(TestForm(), "field", [], msg_prefix=msg_prefix)