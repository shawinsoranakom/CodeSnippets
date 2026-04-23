def test_boolean_field_raises_error_message(self):
        f = models.BooleanField()
        self._test_validation_messages(
            f, "fõo", ["“fõo” value must be either True or False."]
        )