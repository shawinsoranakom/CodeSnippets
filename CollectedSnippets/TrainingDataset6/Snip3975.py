def header_examples(
        data: str | None = Header(
            default=None,
            examples=[
                "header1",
                "header2",
            ],
        ),
    ):
        return data