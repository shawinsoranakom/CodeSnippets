def adaptive_avg_pool2d(self: list[int], out: list[int]):
    if len(out) != 2:
        raise AssertionError(f"Expected out to have length 2, but got {len(out)}")
    if not (len(self) == 3 or len(self) == 4):
        raise AssertionError(
            f"Expected self to have length 3 or 4, but got {len(self)}"
        )
    for i in range(1, len(self)):
        if self[i] == 0:
            raise AssertionError(f"Expected self[{i}] to be non-zero, but got 0")

    shape: list[int] = []
    for i in range(0, len(self) - 2):
        shape.append(self[i])
    for elem in out:
        shape.append(elem)
    return shape