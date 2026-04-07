def test_correct_email_value_passes(self):
        mtv = ModelToValidate(number=10, name="Some Name", email="valid@email.com")
        self.assertIsNone(mtv.full_clean())