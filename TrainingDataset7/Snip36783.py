def test_decimal_field_raises_error_message(self):
        f = models.DecimalField()
        self._test_validation_messages(
            f, "fõo", ["“fõo” value must be a decimal number."]
        )