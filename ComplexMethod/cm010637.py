def broadcast(a: list[int], b: list[int]):
    dimsA = len(a)
    dimsB = len(b)
    ndim = max(dimsA, dimsB)
    expandedSizes: list[int] = []

    for i in range(ndim):
        offset = ndim - 1 - i
        dimA = dimsA - 1 - offset
        dimB = dimsB - 1 - offset
        sizeA = a[dimA] if (dimA >= 0) else 1
        sizeB = b[dimB] if (dimB >= 0) else 1

        if sizeA != sizeB and sizeA != 1 and sizeB != 1:
            # TODO: only assertion error is bound in C++ compilation right now
            raise AssertionError(
                f"The size of tensor a {sizeA} must match the size of tensor b ({sizeB}) at non-singleton dimension {i}"
            )

        expandedSizes.append(sizeB if sizeA == 1 else sizeA)

    return expandedSizes