def butterfly_pattern(n: int) -> str:
    result = []

    for i in range(1, n):
        left_stars = "*" * i
        spaces = " " * (2 * (n - i) - 1)
        right_stars = "*" * i
        result.append(left_stars + spaces + right_stars)

    result.append("*" * (2 * n - 1))

    for i in range(n - 1, 0, -1):
        left_stars = "*" * i
        spaces = " " * (2 * (n - i) - 1)
        right_stars = "*" * i
        result.append(left_stars + spaces + right_stars)

    return "\n".join(result)
