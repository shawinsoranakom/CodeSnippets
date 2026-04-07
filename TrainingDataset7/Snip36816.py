def test_text_greater_that_charfields_max_length_raises_errors(self):
        mtv = ModelToValidate(number=10, name="Some Name" * 100)
        self.assertFailsValidation(mtv.full_clean, ["name"])