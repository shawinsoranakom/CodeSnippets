def test_raises_error_on_multiple_argument_distinct(self):
        message = (
            "StringAgg does not support distinct with multiple expressions on this "
            "database backend."
        )
        with self.assertRaisesMessage(NotSupportedError, message):
            Book.objects.aggregate(
                ratings=StringAgg(
                    Cast(F("rating"), CharField()),
                    Value(";"),
                    distinct=True,
                )
            )