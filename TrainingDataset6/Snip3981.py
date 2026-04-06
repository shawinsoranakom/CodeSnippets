def query_example(
            data: str | None = Query(
                default=None,
                example="query1",
            ),
        ):
            return data