def test_empty_errors_invalid_form(self):
        msg = (
            "The errors of field 'field' on form <TestForm bound=True, valid=False, "
            "fields=(field)> don't match."
        )
        with self.assertRaisesMessage(AssertionError, msg) as ctx:
            self.assertFormError(TestForm.invalid(), "field", [])
        self.assertIn("['invalid value'] != []", str(ctx.exception))