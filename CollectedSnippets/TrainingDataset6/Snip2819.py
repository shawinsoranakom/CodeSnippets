def query_json_list(items: Annotated[Json[list[str]], Query()]) -> list[str]:
    return items