def test_max_whole_digits_validation(self):
        field = models.DecimalField(max_digits=3, decimal_places=1)
        expected_message = validators.DecimalValidator.messages["max_whole_digits"] % {
            "max": 2
        }
        with self.assertRaisesMessage(ValidationError, expected_message):
            field.clean(Decimal("999"), None)