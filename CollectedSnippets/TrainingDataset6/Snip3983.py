def header_example(
            data: str | None = Header(
                default=None,
                example="header1",
            ),
        ):
            return data