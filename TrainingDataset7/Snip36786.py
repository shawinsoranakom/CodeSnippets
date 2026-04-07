def test_datetime_field_raises_error_message(self):
        f = models.DateTimeField()
        # Wrong format
        self._test_validation_messages(
            f,
            "fõo",
            [
                "“fõo” value has an invalid format. It must be in "
                "YYYY-MM-DD HH:MM[:ss[.uuuuuu]][TZ] format."
            ],
        )
        # Correct format but invalid date
        self._test_validation_messages(
            f,
            "2011-10-32",
            [
                "“2011-10-32” value has the correct format (YYYY-MM-DD) but it is an "
                "invalid date."
            ],
        )
        # Correct format but invalid date/time
        self._test_validation_messages(
            f,
            "2011-10-32 10:10",
            [
                "“2011-10-32 10:10” value has the correct format "
                "(YYYY-MM-DD HH:MM[:ss[.uuuuuu]][TZ]) but it is an invalid date/time."
            ],
        )