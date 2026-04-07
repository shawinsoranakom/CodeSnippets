def test_non_form_errors(self):
        self.assertFormSetError(TestFormset.invalid(nonform=True), None, None, "error")