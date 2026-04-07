def test_nullable_boolean_field_raises_error_message(self):
        f = models.BooleanField(null=True)
        self._test_validation_messages(
            f, "fõo", ["“fõo” value must be either True, False, or None."]
        )