def mark_non_differentiable(ctx, output, output_differentiability):
    # Output types are restricted to be:
    # - Tensor
    # - Tensor[]
    # - int, bool, Scalar, float
    # See _check_can_register_backward
    if output_differentiability is not None:
        if not isinstance(output, tuple):
            tuple_output = (output,)
        else:
            tuple_output = output  # type: ignore[assignment]
        if len(output_differentiability) != len(tuple_output):
            raise AssertionError(
                f"output_differentiability length {len(output_differentiability)} "
                f"!= output length {len(tuple_output)}"
            )
        non_differentiable_tensors = []
        for idx, (differentiable, out) in enumerate(
            zip(output_differentiability, tuple_output)
        ):
            if isinstance(out, torch.Tensor):
                if not differentiable:
                    non_differentiable_tensors.append(out)
                continue
            if isinstance(out, list):
                if not differentiable:
                    non_differentiable_tensors.extend(out)
                continue
            if differentiable:
                raise RuntimeError(
                    f"With output_differentiability={output_differentiability}. "
                    f"At idx {idx}, we received an object of type {type(out)} that "
                    f"is not a Tensor, so it cannot have be marked as differentiable in "
                    f"output_differentiability."
                )
        if non_differentiable_tensors:
            ctx.mark_non_differentiable(*non_differentiable_tensors)