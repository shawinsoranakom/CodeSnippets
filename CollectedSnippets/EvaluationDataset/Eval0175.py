def rotate_array(arr: list[int], steps: int) -> list[int]:

    n = len(arr)
    if n == 0:
        return arr

    steps = steps % n

    if steps < 0:
        steps += n

    def reverse(start: int, end: int) -> None:

        while start < end:
            arr[start], arr[end] = arr[end], arr[start]
            start += 1
            end -= 1

    reverse(0, n - 1)
    reverse(0, steps - 1)
    reverse(steps, n - 1)

    return arr
