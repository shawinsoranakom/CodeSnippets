def test_float_field_raises_error_message(self):
        f = models.FloatField()
        self._test_validation_messages(f, "fõo", ["“fõo” value must be a float."])