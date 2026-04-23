def matrix_chain_multiply(arr: list[int]) -> int:
    """
    Find the minimum number of multiplcations required to multiply the chain of matrices

    Args:
        `arr`: The input array of integers.

    Returns:
        Minimum number of multiplications needed to multiply the chain

    Examples:

    >>> matrix_chain_multiply([1, 2, 3, 4, 3])
    30
    >>> matrix_chain_multiply([10])
    0
    >>> matrix_chain_multiply([10, 20])
    0
    >>> matrix_chain_multiply([19, 2, 19])
    722
    >>> matrix_chain_multiply(list(range(1, 100)))
    323398
    >>> # matrix_chain_multiply(list(range(1, 251)))
    # 2626798
    """
    if len(arr) < 2:
        return 0
    # initialising 2D dp matrix
    n = len(arr)
    dp = [[maxsize for j in range(n)] for i in range(n)]
    # we want minimum cost of multiplication of matrices
    # of dimension (i*k) and (k*j). This cost is arr[i-1]*arr[k]*arr[j].
    for i in range(n - 1, 0, -1):
        for j in range(i, n):
            if i == j:
                dp[i][j] = 0
                continue
            for k in range(i, j):
                dp[i][j] = min(
                    dp[i][j], dp[i][k] + dp[k + 1][j] + arr[i - 1] * arr[k] * arr[j]
                )

    return dp[1][n - 1]