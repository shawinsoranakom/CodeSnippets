def dp_count(s, n):
    if n < 0:
        return 0
    table = [0] * (n + 1)

    table[0] = 1

    for coin_val in s:
        for j in range(coin_val, n + 1):
            table[j] += table[j - coin_val]

    return table[n]
