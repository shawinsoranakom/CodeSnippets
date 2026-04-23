def compute_elementwise_output_logical_to_physical_perm(
    *tensors, _skip_checks=False, ambiguity_check=False
) -> tuple[list[int], bool]:
    from torch.fx.experimental.symbolic_shapes import guard_or_false

    if not _skip_checks and len(tensors) == 0:
        msg = "Can't compute elementwise output strides for zero tensors!"
        raise ValueError(msg)

    if not _skip_checks:
        check_same_shape(*tensors, allow_cpu_scalar_tensors=True)

    # Filters the tensors to actual tensors
    if not _skip_checks:
        tensors = tuple(
            a
            for a in tensors
            if isinstance(a, TensorLike) and not is_cpu_scalar_tensor(a)
        )

    # Short-circuits for CPU scalar case
    if len(tensors) == 0:
        return [], False

    # Short-circuits for shapes with zero or one dimensions
    # TODO: are these necessary?
    ndim = tensors[0].ndim
    if ndim == 0:
        return [], False
    if ndim == 1:
        return [0], False

    # Short-circuits if contiguous or channels last, following the fake fast path.
    # This reduces the number of guards we end up making
    is_contiguous = True
    is_channels_last = True
    for t in tensors:
        is_contiguous = is_contiguous and is_contiguous_for_memory_format_or_false(
            t, memory_format=torch.contiguous_format
        )
        is_channels_last = (
            is_channels_last
            and is_contiguous_for_memory_format_or_false(
                t, memory_format=torch.channels_last
            )
        )

    if is_contiguous and not is_channels_last:
        return list(range(ndim)), False

    if is_channels_last and not is_contiguous:
        return [0, *list(range(2, ndim)), 1], False

    shape = tensors[0].shape

    def should_swap(idx_a, idx_b):
        def ge(a, b):
            """
            Returns true if a is symbolically greater than or equal to b, assuming a >= 0, b >= 0.
            """
            if guard_or_false(b == 0):
                return True
            elif guard_or_false(a == 0):
                return False
            return guard_or_false(a >= b) or guard_or_false(a % b == 0)

        for tensor in tensors:
            stride_a = tensor.stride()[idx_a]
            stride_b = tensor.stride()[idx_b]

            if guard_or_false(stride_a == 0) or guard_or_false(stride_b == 0):
                continue

            if guard_or_false(stride_a == stride_b):
                if ge(shape[idx_b], shape[idx_a]):
                    continue
                return 1

            if ge(stride_b, stride_a):
                return -1

            if ge(stride_a, stride_b):
                return 1

        # Note: this case is hit if all strides are zero,
        # or all strides are equal and all dimensions have the same length
        return 0

    # The "sort" order for the permutation is back-to-front, but
    # the natural order for permutations is front-to-back.  Do the
    # sorting back-to-front and then reverse it on output.
    #
    # also, note this returns the logical to physical shape permutation
    perm = list(reversed(range(ndim)))

    # insertion sort with support for ambiguous comparisons
    for i in range(1, ndim):
        dim1 = i
        for dim0 in reversed(range(i)):
            comparison = should_swap(perm[dim0], perm[dim1])
            if comparison > 0:
                perm[dim0], perm[dim1] = perm[dim1], perm[dim0]
                dim1 = dim0
            elif comparison < 0:
                break

    # verify we've imposed ordering if ambiguity_check=True
    raise_ambiguous = False
    if ambiguity_check:
        for i, j in zip(range(ndim - 1), range(1, ndim)):
            order = should_swap(perm[i], perm[j])
            if order != -1:
                raise_ambiguous = True
                break

    return list(reversed(perm)), raise_ambiguous