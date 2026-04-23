def test_non_form_errors_with_field(self):
        msg = "You must use field=None with form_index=None."
        with self.assertRaisesMessage(ValueError, msg):
            self.assertFormSetError(
                TestFormset.invalid(nonform=True), None, "field", "error"
            )