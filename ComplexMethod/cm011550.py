def pointwise_rule(op_schema: OpSchema, linearity: bool = False) -> OutputSharding:
    """
    Propagate the sharding for pointwise operations.

    Examples:
        ij,ij->ij - addition/mul
        ij,j->ij - broadcasted addition
    """
    alphabet = string.ascii_lowercase
    # find the max_dim first in case we need to broadcasting
    input_specs = op_schema.args_spec
    max_dim = max(input.ndim for input in input_specs)
    dimchars = []
    singleton_counter: list[int] = [0] * max_dim
    for input in input_specs:
        start_dim = max_dim - input.ndim
        p = alphabet[start_dim:max_dim]
        # handle the "broadcasting to a common shape case"
        # see https://pytorch.org/docs/stable/notes/broadcasting.html
        # If any of the dimensions is singleton dimension (i.e. 1).
        # we mark the dim char as a special "1" to distinguish with
        # the non-singleton dimension, so that sharding propagation
        # should just ignore the singleton dimension.
        if len(input_specs) > 1:
            for i in range(max_dim):
                if i < start_dim:
                    # treat the leading miss dim chars as singleton
                    singleton_counter[i] += 1
                elif input.shape[i - start_dim] == 1:
                    # mark singleton dim char as a special "1" in einop rule
                    singleton_counter[i] += 1
                    p = _replace_char_in_str(p, "1", (i - start_dim))

        dimchars.append(p)
    out_dimchars = alphabet[:max_dim]
    # check if we replace the all inputs dim char with singleton dimension,
    # if we replace all inputs, we also need to replace the output dimension.
    for output_dim_idx in range(len(out_dimchars)):
        if singleton_counter[output_dim_idx] == len(input_specs):
            out_dimchars = _replace_char_in_str(out_dimchars, "1", output_dim_idx)

    fmt = f"{','.join(p for p in dimchars)}->{out_dimchars}"

    enforce_sharding: dict[str, int] = {}
    if op_schema.is_inplace_op():
        follow_spec = op_schema.args_spec[0]
        enforce_sharding.update(zip(out_dimchars, follow_spec.dim_map))
    elif op_schema.is_out_variant_op():
        follow_spec = cast(DTensorSpec, op_schema.kwargs_schema["out"])
        enforce_sharding.update(zip(out_dimchars, follow_spec.dim_map))

    return einop_rule(
        fmt,
        op_schema,
        linearity=linearity,
        enforce_sharding=enforce_sharding,
    )