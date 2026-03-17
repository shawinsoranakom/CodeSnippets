def trapped_rainwater(heights: tuple[int, ...]) -> int:
    if not heights:
        return 0
    if any(h < 0 for h in heights):
        raise ValueError("No height can be negative")
    length = len(heights)

    left_max = [0] * length
    left_max[0] = heights[0]
    for i, height in enumerate(heights[1:], start=1):
        left_max[i] = max(height, left_max[i - 1])

    right_max = [0] * length
    right_max[-1] = heights[-1]
    for i in range(length - 2, -1, -1):
        right_max[i] = max(heights[i], right_max[i + 1])

    return sum(
        min(left, right) - height
        for left, right, height in zip(left_max, right_max, heights)
    )
