def form_json_list(items: Annotated[Json[list[str]], Form()]) -> list[str]:
    return items