def test_wrong_email_value_raises_error(self):
        mtv = ModelToValidate(number=10, name="Some Name", email="not-an-email")
        self.assertFailsValidation(mtv.full_clean, ["email"])