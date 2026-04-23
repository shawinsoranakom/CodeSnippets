def _check_inputs(tupled_inputs) -> bool:
    # Make sure that gradients are saved for at least one input
    any_input_requiring_grad = False
    for idx, inp in enumerate(tupled_inputs):
        if is_tensor_like(inp) and inp.requires_grad:
            if not (inp.dtype == torch.float64 or inp.dtype == torch.complex128):
                warnings.warn(
                    f"Input #{idx} requires gradient and "
                    "is not a double precision floating point or complex. "
                    "This check will likely fail if all the inputs are "
                    "not of double precision floating point or complex. ",
                    stacklevel=2,
                )
            if inp.is_sparse:
                content = inp._values()
            elif _is_sparse_compressed_tensor(inp):
                content = inp.values()
            else:
                content = inp
            # TODO: To cover more problematic cases, replace stride = 0 check with
            # "any overlap in memory" once we have a proper function to check it.
            if content.layout is not torch._mkldnn:  # type: ignore[attr-defined]
                if not all(
                    st > 0 or sz <= 1
                    for st, sz in zip(content.stride(), content.size())
                ):
                    raise RuntimeError(
                        f"The {idx}th input has a dimension with stride 0. gradcheck only "
                        "supports inputs that are non-overlapping to be able to "
                        "compute the numerical gradients correctly. You should call "
                        ".contiguous on the input before passing it to gradcheck."
                    )
            any_input_requiring_grad = True

    if not any_input_requiring_grad:
        raise ValueError(
            "gradcheck expects at least one input tensor to require gradient, "
            "but none of the them have requires_grad=True."
        )
    return True