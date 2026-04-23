def _broadcast_shapes(*_shapes):
    from torch.fx.experimental.symbolic_shapes import (
        guard_or_false,
        guarding_hint_or_throw,
        has_guarding_hint,
        is_nested_int,
    )

    backed_so = torch.fx.experimental._config.backed_size_oblivious

    shapes = tuple(
        (x,) if isinstance(x, IntLike) else x
        for x in filter(lambda x: x is not None, _shapes)
    )

    # Short-circuits on no input
    if len(shapes) == 0:
        return None

    for shape in shapes:
        if not isinstance(shape, Sequence):
            raise RuntimeError(
                f"Input shapes should be of type ints, a tuple of ints, or a list of ints, got {shape}"
            )

    # Computes common shape
    common_shape: list[int | torch.SymInt] = [
        1,
    ] * reduce(max, (len(shape) for shape in shapes))
    for arg_idx, shape in enumerate(shapes):
        for idx in range(-1, -1 - len(shape), -1):
            # NB: handle nested ints specially to avoid invalid guarding on Ne(j0, 1).
            if is_nested_int(shape[idx]):
                # Broadcasting is allowed for (j0, 1) or (j0, j0);
                # not (j0, j1), (j0, 5), etc.
                if is_nested_int(common_shape[idx]) and guard_or_false(
                    shape[idx] == common_shape[idx]
                ):
                    continue
            else:
                # When backed size oblivious is used, we specialize for broadcasting
                # if its the only way to compile the example input.
                # i.e: s0:1, s1:1 ==>
                #           assert s0==s1, no specialization on ==1 or !=1.
                #            The non-broadcast path is picked
                #      s0:1, s1:4 ==>
                #           specialize(s0) to be 1.
                #      s0:4, s1:1 ==>
                #           specialize(s1) to be 1.
                if (
                    backed_so
                    and has_guarding_hint(shape[idx])
                    and has_guarding_hint(common_shape[idx])
                ):
                    a = guarding_hint_or_throw(shape[idx])
                    b = guarding_hint_or_throw(common_shape[idx])
                    if a == 1 and b != 1:
                        torch._check(shape[idx] == 1)
                    if b == 1 and a != 1:
                        torch._check(common_shape[idx] == 1)
                if guard_or_false(shape[idx] == common_shape[idx]):
                    continue

            if guard_or_false(common_shape[idx] == 1):
                if shape[idx] < 0:
                    raise ValueError(
                        "Attempting to broadcast a dimension with negative length!"
                    )
                common_shape[idx] = shape[idx]

            if not is_nested_int(shape[idx]) and guard_or_false(shape[idx] == 1):
                # broadcast case .
                continue
            else:
                # If broadcasting is undecided we pick non-broadcast path and add runtime assertion.
                torch._check(
                    common_shape[idx] == shape[idx],
                    lambda: f"Attempting to broadcast a dimension of length {shape[idx]} at {idx}! "
                    f"Mismatching argument at index {arg_idx} had {shape}; but expected shape "
                    f"should be broadcastable to {common_shape}",
                )

    return common_shape