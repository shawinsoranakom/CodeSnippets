def test_non_field_errors(self):
        self.assertFormSetError(
            TestFormset.invalid(nonfield=True), 0, None, "non-field error"
        )