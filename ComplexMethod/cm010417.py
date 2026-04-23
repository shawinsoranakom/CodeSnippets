def _inline_asm_dense(*inputs, asm_str, constraints, dtype, is_pure, pack):
    if not inputs:
        raise ValueError("inline_asm_elementwise requires at least one input tensor")

    inputs = torch.broadcast_tensors(*inputs)

    if not inputs[0].is_cuda:
        raise RuntimeError("inline_asm_elementwise only supports CUDA tensors")

    if pack > 1:
        raise RuntimeError(
            "inline_asm_elementwise with pack > 1 requires torch.compile"
        )

    n_outputs, n_inputs = _parse_constraints(constraints)

    if n_outputs != 1:
        raise ValueError(f"Expected 1 output constraint, got {n_outputs}")

    if n_inputs != len(inputs):
        raise ValueError(
            f"Constraint string specifies {n_inputs} inputs but got "
            f"{len(inputs)} tensor(s)"
        )

    # Jiterator generates a single input type for all inputs — mixed dtypes
    # would produce incorrect CUDA code.
    input_dtypes = {inp.dtype for inp in inputs}
    if len(input_dtypes) > 1:
        raise ValueError(
            f"All inputs must have the same dtype for eager execution, "
            f"got {sorted(str(d) for d in input_dtypes)}"
        )

    jit_fn = _get_jiterator_fn(
        asm_str=asm_str,
        constraints=constraints,
        n_inputs=len(inputs),
        input_dtype=inputs[0].dtype,
        output_dtype=dtype,
    )

    return jit_fn(*inputs)