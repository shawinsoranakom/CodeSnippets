def minimax(
    depth: int, node_index: int, is_max: bool, scores: list[int], height: float
) -> int:

    if depth < 0:
        raise ValueError("Depth cannot be less than 0")
    if len(scores) == 0:
        raise ValueError("Scores cannot be empty")

    if depth == height:
        return scores[node_index]

    if is_max:
        return max(
            minimax(depth + 1, node_index * 2, False, scores, height),
            minimax(depth + 1, node_index * 2 + 1, False, scores, height),
        )

    return min(
        minimax(depth + 1, node_index * 2, True, scores, height),
        minimax(depth + 1, node_index * 2 + 1, True, scores, height),
    )
