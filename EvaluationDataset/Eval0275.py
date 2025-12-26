def binary_tree_count(node_count: int) -> int:
    return catalan_number(node_count) * factorial(node_count)

