def test_time_field_raises_error_message(self):
        f = models.TimeField()
        # Wrong format
        self._test_validation_messages(
            f,
            "fõo",
            [
                "“fõo” value has an invalid format. It must be in HH:MM[:ss[.uuuuuu]] "
                "format."
            ],
        )
        # Correct format but invalid time
        self._test_validation_messages(
            f,
            "25:50",
            [
                "“25:50” value has the correct format (HH:MM[:ss[.uuuuuu]]) but it is "
                "an invalid time."
            ],
        )