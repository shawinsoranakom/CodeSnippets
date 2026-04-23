def expand(a: Tensor, *shape, implicit: bool = False) -> Tensor:
    from torch.fx.experimental.symbolic_shapes import (
        guard_or_false,
        guarding_hint_or_throw,
        has_guarding_hint,
        sym_or,
    )

    backed_so = torch.fx.experimental._config.backed_size_oblivious

    # NOTE: cannot use utils.extract_shape_from_varargs here
    # because that also validates the shape, but the shape
    # given to expand may be "invalid"
    if len(shape) == 1 and isinstance(shape[0], Sequence):
        shape = tuple(shape[0])

    torch._check(
        len(shape) >= len(a.shape),
        lambda: "expand: the requested shape has too few dimensions!",
    )

    offset = len(shape) - len(a.shape)
    shape_ = list(shape)
    for idx, x in enumerate(a.shape):
        offset_idx = idx + offset
        requested_length = shape[offset_idx]

        # expand(in -> out) has 3 different semantics:
        # 1) out == -1 -> size = in, stride unchanged
        # 2) in == 1 -> size = out, stride = 0
        # 3) in == out -> size = in, stride unchanged
        #
        # the code below is written for unbacked semantics s.t. we assume unbacked symbols don't
        # represent -1 unless explicitly specified, and the user is opting for case 2) or 3).
        # the sym_or allows either case, but in the decomposition's current state, broadcast_in_dim()
        # will either assume case 3) (via validate_shape() marking the expanded shape size-like), or will
        # raise a data-dependent error trying to figure out if the stride is 0, requiring the user to manually
        # select between the semantics of cases 2) and 3).
        if guard_or_false(requested_length == -1):
            shape_[offset_idx] = x
        else:
            # When backed size oblivious is used, we specialize for broadcasting
            # if its the only way to compile the example input.
            # i.e: x:1, requested_length:1 ==>
            #           assert x==requested_length, no specialization on ==1 or !=1.
            #            The non-broadcast path is picked
            #      x:1, requested_length:4 ==>
            #           specialize(x) to be 1.
            if (
                backed_so
                and has_guarding_hint(x)
                and has_guarding_hint(requested_length)
            ):
                x_hint = guarding_hint_or_throw(x)
                requested_hint = guarding_hint_or_throw(requested_length)
                if x_hint == 1 and requested_hint != 1:
                    torch._check(x == 1)

            torch._check(
                sym_or(x == 1, requested_length == x),
                lambda: f"expand: attempting to expand a dimension of length {x} -> {requested_length}!",
            )
            torch._check(requested_length >= 0)
            shape_[offset_idx] = requested_length

    # At this point shape must be valid
    utils.validate_shape(shape_)

    return prims.broadcast_in_dim(
        a, shape_, tuple(range(offset, len(a.shape) + offset))
    )