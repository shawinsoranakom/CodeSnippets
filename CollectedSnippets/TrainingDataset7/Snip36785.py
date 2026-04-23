def test_date_field_raises_error_message(self):
        f = models.DateField()
        self._test_validation_messages(
            f,
            "fõo",
            [
                "“fõo” value has an invalid date format. It must be in YYYY-MM-DD "
                "format."
            ],
        )
        self._test_validation_messages(
            f,
            "aaaa-10-10",
            [
                "“aaaa-10-10” value has an invalid date format. It must be in "
                "YYYY-MM-DD format."
            ],
        )
        self._test_validation_messages(
            f,
            "2011-13-10",
            [
                "“2011-13-10” value has the correct format (YYYY-MM-DD) but it is an "
                "invalid date."
            ],
        )
        self._test_validation_messages(
            f,
            "2011-10-32",
            [
                "“2011-10-32” value has the correct format (YYYY-MM-DD) but it is an "
                "invalid date."
            ],
        )