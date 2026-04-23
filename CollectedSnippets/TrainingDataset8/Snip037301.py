def make_delta_path(
    root_container: int, parent_path: Tuple[int, ...], index: int
) -> List[int]:
    delta_path = [root_container]
    delta_path.extend(parent_path)
    delta_path.append(index)
    return delta_path