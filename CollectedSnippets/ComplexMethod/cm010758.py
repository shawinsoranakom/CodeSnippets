def reductify_leaf(
    grad_input: torch.Tensor | None,
    grad_input_bdim: int | None,
    input_bdim: int | None,
    batch_size: int,
    target_shape_without_bdim_to_reduce_to: Any = None,
) -> torch.Tensor | None:
    if grad_input is None:
        return None

    if grad_input_bdim is None and input_bdim is None:
        return grad_input

    if grad_input_bdim is not None and input_bdim is None:
        return grad_input.sum(grad_input_bdim)

    # NOTE: [Why can't we rely on autograd to reduce expanded gradients?]
    # For reverse-mode AD,
    # given a grad_input and input, it is valid for the user to return a
    # grad_input that has a broadcasted shape when compared to the input.
    # In this situation, autograd automatically reduces the grad_input to
    # the shape of the input.
    #
    # However, when input_bdim is not None, we have problems.
    #
    # [example 1]
    # grad_input: Tensor[3, 4], input: Tensor[B, 4]
    # We can expand grad_input to Tensor[B, 3, 4], but that isn't broadcastable
    # from [B, 4].
    #
    # [example 2]
    # grad_input: Tensor[3, B, 4], input: Tensor[B, 4]
    # We can swizzle grad_input to Tensor[B, 3, 4], but that isn't broadcastable
    # from [B, 4].
    #
    # This means that we need to also reduce the grad_input to the shape of the
    # input. This behavior is controlled by the `target_shape_without_bdim_to_reduce_to` flag;
    # if not-None then we do the reducing manually, otherwise, we do not do a reduction.
    if input_bdim is None:
        raise AssertionError("input_bdim must not be None")

    if grad_input_bdim is None:
        grad_input = grad_input.unsqueeze(input_bdim)
        new_shape = list(grad_input.shape)
        new_shape[input_bdim] = batch_size
        grad_input = grad_input.expand(new_shape)
        grad_input_bdim = input_bdim

    if target_shape_without_bdim_to_reduce_to is not None:
        return vmap(
            torch.Tensor.sum_to_size,
            in_dims=(grad_input_bdim, None),
            out_dims=input_bdim,
        )(grad_input, target_shape_without_bdim_to_reduce_to)

    if input_bdim != grad_input_bdim:
        grad_input = grad_input.movedim(grad_input_bdim, input_bdim)
    return grad_input