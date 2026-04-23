def quantile(node: Node | None, index: int, start: int, end: int) -> int:
    """
    Returns the index'th smallest element in interval [start, end] in the list
    index is 0-indexed

    >>> root = build_tree(test_array)
    >>> quantile(root, 2, 2, 5)
    5
    >>> quantile(root, 5, 2, 13)
    4
    >>> quantile(root, 0, 6, 6)
    8
    >>> quantile(root, 4, 2, 5)
    -1
    """
    if index > (end - start) or start > end or node is None:
        return -1
    # Leaf node case
    if node.minn == node.maxx:
        return node.minn
    # Number of elements in the left subtree in interval [start, end]
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