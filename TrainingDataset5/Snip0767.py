def longest_subsequence(array: list[int]) -> list[int]:
    n = len(array)
    longest_increasing_subsequence = []
    for i in range(n):
        longest_increasing_subsequence.append([array[i]])

    for i in range(1, n):
        for prev in range(i):
            if array[prev] <= array[i] and len(
                longest_increasing_subsequence[prev]
            ) + 1 > len(longest_increasing_subsequence[i]):
                longest_increasing_subsequence[i] = copy.copy(
                    longest_increasing_subsequence[prev]
                )
                longest_increasing_subsequence[i].append(array[i])

    result: list[int] = []
    for i in range(n):
        if len(longest_increasing_subsequence[i]) > len(result):
            result = longest_increasing_subsequence[i]

    return result
