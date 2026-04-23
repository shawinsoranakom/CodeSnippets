def query(sparse_table: list[list[int]], left_bound: int, right_bound: int) -> int:

    if left_bound < 0 or right_bound >= len(sparse_table[0]):
        raise IndexError("list index out of range")

    j = int(log2(right_bound - left_bound + 1))

    return min(sparse_table[j][right_bound - (1 << j) + 1], sparse_table[j][left_bound])
