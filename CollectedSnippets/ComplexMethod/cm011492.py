def dim_movedim(
    ndim: int,
    input: DimsType,
    destination: DimsType,
) -> DimMap:
    input = normalize_dims(input, ndim)
    destination = normalize_dims(destination, ndim)

    if not len(input) == len(destination):
        raise AssertionError(
            f"Expected len(input) == len(destination), got {len(input)} != {len(destination)}"
        )
    input_set = set(input)
    if not len(input_set) == len(input):
        raise AssertionError("Found repeated input dims")
    if not len(set(destination)) == len(destination):
        raise AssertionError("Found repeated output dims")
    if not max(input) < ndim:
        raise AssertionError(f"Expected max(input) < ndim, got {max(input)} >= {ndim}")
    if not max(destination) < ndim:
        raise AssertionError(
            f"Expected max(destination) < ndim, got {max(destination)} >= {ndim}"
        )

    dest = [-1] * ndim
    for i, d in zip(input, destination):
        dest[d] = i

    unused_inputs_iter = iter(i for i in range(ndim) if i not in input_set)
    for i in range(ndim):
        if dest[i] == -1:
            dest[i] = next(unused_inputs_iter)

    return tuple(InputDim(i) for i in dest)