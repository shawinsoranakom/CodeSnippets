def get_query_type_optional(query: int | None = None):
    if query is None:
        return "foo bar"
    return f"foo bar {query}"