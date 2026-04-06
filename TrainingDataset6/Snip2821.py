def cookie_json_list(items: Annotated[Json[list[str]], Cookie()]) -> list[str]:
    return items