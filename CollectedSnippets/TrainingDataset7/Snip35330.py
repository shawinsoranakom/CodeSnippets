def test_error_list(self):
        self.assertFormSetError(TestFormset.invalid(), 0, "field", ["invalid value"])