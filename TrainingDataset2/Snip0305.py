def quantile(node: Node | None, index: int, start: int, end: int) -> int:
    if index > (end - start) or start > end or node is None:
        return -1
    if node.minn == node.maxx:
        return node.minn
    num_elements_in_left_tree = node.map_left[end] - (
        node.map_left[start - 1] if start else 0
    )
    if num_elements_in_left_tree > index:
        return quantile(
            node.left,
            index,
            (node.map_left[start - 1] if start else 0),
            node.map_left[end] - 1,
        )
    else:
        return quantile(
            node.right,
            index - num_elements_in_left_tree,
            start - (node.map_left[start - 1] if start else 0),
            end - node.map_left[end],
        )
