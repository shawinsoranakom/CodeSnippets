def test_error_list(self):
        self.assertFormError(TestForm.invalid(), "field", ["invalid value"])