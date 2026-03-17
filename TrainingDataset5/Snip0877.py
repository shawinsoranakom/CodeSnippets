def construct_path(current: int | None, parents: dict[int, int | None]) -> list[int]:
    path: list[int] = []
    while current is not None:
        path.append(current)
        current = parents[current]
    return path
