def _make_grads(
    outputs: Sequence[torch.Tensor] | Sequence[graph.GradientEdge],
    grads: Sequence[_OptionalTensor],
    is_grads_batched: bool,
) -> tuple[_OptionalTensor, ...]:
    new_grads: list[_OptionalTensor] = []

    for out, grad in zip(outputs, grads):
        # pyrefly: ignore [redundant-cast]
        out = cast(torch.Tensor | graph.GradientEdge, out)
        out_size = None
        out_device = None

        if isinstance(out, graph.GradientEdge):
            out_metadata = out.node._input_metadata[out.output_nr]
            out_size = torch.Size(out_metadata.shape)
            out_dtype = out_metadata.dtype
            out_device = out_metadata.device
            out_is_nested = out_metadata.is_nested_tensor
            if out_metadata.is_cpp_nested_tensor:
                raise RuntimeError(
                    "C++ NestedTensor are not supported with GradientEdge"
                )
            out_is_cpp_nested = False
        else:
            # circular import
            from torch.nested._internal.nested_tensor import NestedTensor

            if not isinstance(out, torch.Tensor):
                raise AssertionError("Expected output to be a torch.Tensor")
            out_dtype = out.dtype
            out_is_nested = out.is_nested
            out_is_cpp_nested = out_is_nested and not isinstance(out, NestedTensor)
            if not out_is_cpp_nested:
                out_size = out.shape

        if isinstance(grad, torch.Tensor):
            from torch.fx.experimental.symbolic_shapes import expect_true, sym_eq

            first_grad = grad if not is_grads_batched else grad[0]

            # TODO: We can remove this conditional once we uniformly use
            # singleton int to represent jagged dimension, so that size() call
            # on nested tensor works.
            if out_is_cpp_nested:
                if not isinstance(out, torch.Tensor):
                    raise AssertionError("Expected output to be a torch.Tensor.")
                shape_matches = torch.is_same_size(out, first_grad)
            else:
                # We need to do a regular size check, without going through
                # the operator, to be able to handle unbacked symints
                # (expect_true ensures we can deal with unbacked)
                if out_size is None:
                    raise AssertionError("Expected out_size to be set.")
                shape_matches = expect_true(sym_eq(out_size, first_grad.size()))

            if not shape_matches:
                out = cast(torch.Tensor | graph.GradientEdge, out)  # type: ignore[redundant-cast]
                out_shape, grad_shape = _calculate_shape(
                    out, first_grad, is_grads_batched
                )
                if is_grads_batched:
                    raise RuntimeError(
                        "If `is_grads_batched=True`, we interpret the first "
                        "dimension of each grad_output as the batch dimension. "
                        "The sizes of the remaining dimensions are expected to match "
                        "the shape of corresponding output, but a mismatch "
                        "was detected: grad_output["
                        + str(grads.index(grad))
                        + "] has a shape of "
                        + str(grad_shape)
                        + " and output["
                        + str(outputs.index(out))
                        + "] has a shape of "
                        + str(out_shape)
                        + ". "
                        "If you only want some tensors in `grad_output` to be considered "
                        "batched, consider using vmap."
                    )
                else:
                    raise RuntimeError(
                        "Mismatch in shape: grad_output["
                        + str(grads.index(grad))
                        + "] has a shape of "
                        + str(grad_shape)
                        + " and output["
                        + str(outputs.index(out))
                        + "] has a shape of "
                        + str(out_shape)
                        + "."
                    )
            if out_dtype.is_complex != grad.dtype.is_complex:
                raise RuntimeError(
                    "For complex Tensors, both grad_output and output"
                    " are required to have the same dtype."
                    " Mismatch in dtype: grad_output["
                    + str(grads.index(grad))
                    + "] has a dtype of "
                    + str(grad.dtype)
                    + " and output["
                    + str(outputs.index(out))
                    + "] has a dtype of "
                    + str(out_dtype)
                    + "."
                )
            new_grads.append(grad)
        elif grad is None:
            if isinstance(out, graph.GradientEdge) or out.requires_grad:  # type: ignore[attr-defined]
                if isinstance(out, graph.GradientEdge):
                    if out_size is None:
                        raise AssertionError("Expected out_size to be set.")
                    out_numel_is_1 = all(o == 1 for o in out_size)
                else:
                    if not isinstance(out, torch.Tensor):
                        raise AssertionError("Expected output to be a torch.Tensor")
                    out_numel_is_1 = out.numel() == 1
                if not out_numel_is_1:
                    raise RuntimeError(
                        "grad can be implicitly created only for scalar outputs"
                    )
                if not out_dtype.is_floating_point:
                    msg = (
                        "grad can be implicitly created only for real scalar outputs"
                        f" but got {out_dtype}"
                    )
                    raise RuntimeError(msg)
                if isinstance(out, graph.GradientEdge):
                    if out_size is None:
                        raise AssertionError("Expected out_size to be set.")
                    if out_device is None:
                        raise AssertionError("Expected out_device to be set.")
                    new_grads.append(
                        torch.ones(
                            out_size,
                            dtype=out_dtype,
                            device=out_device,
                        )
                    )
                else:
                    if not isinstance(out, torch.Tensor):
                        raise AssertionError("Expected output to be a torch.Tensor")
                    new_grads.append(
                        torch.ones_like(out, memory_format=torch.preserve_format)
                    )
            else:
                new_grads.append(None)
        else:
            raise TypeError(
                "gradients can be either Tensors or None, but got "
                + type(grad).__name__
            )
    return tuple(new_grads)