def test_field_validators_can_be_any_iterable(self):
        mtv = ModelToValidate(
            number=10,
            name="Some Name",
            f_with_custom_validator=42,
            f_with_iterable_of_validators=12,
        )
        self.assertFailsValidation(mtv.full_clean, ["f_with_iterable_of_validators"])
        self.assertFieldFailsValidationWithMessage(
            mtv.full_clean,
            "f_with_iterable_of_validators",
            ["This is not the answer to life, universe and everything!"],
        )