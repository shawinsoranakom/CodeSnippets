def header_json_list(x_items: Annotated[Json[list[str]], Header()]) -> list[str]:
    return x_items