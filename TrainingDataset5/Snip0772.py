def matrix_chain_order(array: list[int]) -> tuple[list[list[int]], list[list[int]]]:
    n = len(array)
    matrix = [[0 for _ in range(n)] for _ in range(n)]
    sol = [[0 for _ in range(n)] for _ in range(n)]

    for chain_length in range(2, n):
        for a in range(1, n - chain_length + 1):
            b = a + chain_length - 1

            matrix[a][b] = sys.maxsize
            for c in range(a, b):
                cost = (
                    matrix[a][c] + matrix[c + 1][b] + array[a - 1] * array[c] * array[b]
                )
                if cost < matrix[a][b]:
                    matrix[a][b] = cost
                    sol[a][b] = c
    return matrix, sol
