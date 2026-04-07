def test_integer_field_raises_error_message(self):
        f = models.IntegerField()
        self._test_validation_messages(f, "fõo", ["“fõo” value must be an integer."])