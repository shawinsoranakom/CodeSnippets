def test_single_error(self):
        self.assertFormError(TestForm.invalid(), "field", "invalid value")