def range_counting(
    node: Node | None, start: int, end: int, start_num: int, end_num: int
) -> int:
    if (
        start > end
        or node is None
        or start_num > end_num
        or node.minn > end_num
        or node.maxx < start_num
    ):
        return 0
    if start_num <= node.minn and node.maxx <= end_num:
        return end - start + 1
    left = range_counting(
        node.left,
        (node.map_left[start - 1] if start else 0),
        node.map_left[end] - 1,
        start_num,
        end_num,
    )
    right = range_counting(
        node.right,
        start - (node.map_left[start - 1] if start else 0),
        end - node.map_left[end],
        start_num,
        end_num,
    )
    return left + right
