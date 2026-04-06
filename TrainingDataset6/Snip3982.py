def query_example_examples(
            data: str | None = Query(
                default=None,
                example="query_overridden",
                examples=["query1", "query2"],
            ),
        ):
            return data