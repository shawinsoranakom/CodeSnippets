def matrix_chain_order(dims: list[int]) -> int:

    @cache
    def a(i: int, j: int) -> int:
        return min(
            (a(i, k) + dims[i] * dims[k] * dims[j] + a(k, j) for k in range(i + 1, j)),
            default=0,
        )

    return a(0, len(dims) - 1)
