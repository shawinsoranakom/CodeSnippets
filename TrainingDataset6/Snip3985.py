def cookie_example(
            data: str | None = Cookie(
                default=None,
                example="cookie1",
            ),
        ):
            return data