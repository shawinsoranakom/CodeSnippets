def rank(node: Node | None, num: int, start: int, end: int) -> int:
    if start > end:
        return 0
    rank_till_end = rank_till_index(node, num, end)
    rank_before_start = rank_till_index(node, num, start - 1)
    return rank_till_end - rank_before_start
