def catalan_number(node_count: int) -> int:
    return binomial_coefficient(2 * node_count, node_count) // (node_count + 1)
