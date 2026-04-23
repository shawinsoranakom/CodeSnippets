def cookie_examples(
        data: str | None = Cookie(
            default=None,
            examples=["cookie1", "cookie2"],
        ),
    ):
        return data