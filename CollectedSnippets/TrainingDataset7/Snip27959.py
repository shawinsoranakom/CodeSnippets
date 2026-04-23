def test_backend_range_validation(self):
        """
        Backend specific ranges are enforced at the model validation level
        (#12030).
        """
        min_value, max_value = self.backend_range

        if min_value is not None:
            instance = self.model(value=min_value - 1)
            expected_message = validators.MinValueValidator.message % {
                "limit_value": min_value,
            }
            with self.assertRaisesMessage(ValidationError, expected_message):
                instance.full_clean()
            instance.value = min_value
            instance.full_clean()

        if max_value is not None:
            instance = self.model(value=max_value + 1)
            expected_message = validators.MaxValueValidator.message % {
                "limit_value": max_value,
            }
            with self.assertRaisesMessage(ValidationError, expected_message):
                instance.full_clean()
            instance.value = max_value
            instance.full_clean()