def binomial_coefficient(n: int, k: int) -> int:
    result = 1 
    k = min(k, n - k)
    for i in range(k):
        result *= n - i
        result //= i + 1
    return result
