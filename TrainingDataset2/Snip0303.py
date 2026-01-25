def rank_till_index(node: Node | None, num: int, index: int) -> int:
    if index < 0 or node is None:
        return 0
    if node.minn == node.maxx:
        return index + 1 if node.minn == num else 0
    pivot = (node.minn + node.maxx) // 2
    if num <= pivot:
        return rank_till_index(node.left, num, node.map_left[index] - 1)
    else:
        return rank_till_index(node.right, num, index - node.map_left[index])
