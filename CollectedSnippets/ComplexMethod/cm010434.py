def as_nested_tensor(
    ts: Tensor | list[Tensor] | tuple[Tensor, ...],
    dtype: DType | None = None,
    device: Device | None = None,
    layout=None,
) -> Tensor:
    r"""
    Constructs a nested tensor preserving autograd history from a tensor or a list / tuple of
    tensors.

    If a nested tensor is passed, it will be returned directly unless the device / dtype / layout
    differ. Note that converting device / dtype will result in a copy, while converting layout
    is not currently supported by this function.

    If a non-nested tensor is passed, it is treated as a batch of constituents of consistent size.
    A copy will be incurred if the passed device / dtype differ from those of the input OR if
    the input is non-contiguous. Otherwise, the input's storage will be used directly.

    If a tensor list is provided, tensors in the list are always copied during construction of
    the nested tensor.

    Args:
        ts (Tensor or List[Tensor] or Tuple[Tensor]): a tensor to treat as a nested tensor OR a
            list / tuple of tensors with the same ndim

    Keyword arguments:
        dtype (:class:`torch.dtype`, optional): the desired type of returned nested tensor.
            Default: if None, same :class:`torch.dtype` as leftmost tensor in the list.
        device (:class:`torch.device`, optional): the desired device of returned nested tensor.
            Default: if None, same :class:`torch.device` as leftmost tensor in the list
        layout (:class:`torch.layout`, optional): the desired layout of returned nested tensor.
            Only strided and jagged layouts are supported. Default: if None, the strided layout.

    Example::

        >>> a = torch.arange(3, dtype=torch.float, requires_grad=True)
        >>> b = torch.arange(5, dtype=torch.float, requires_grad=True)
        >>> nt = torch.nested.as_nested_tensor([a, b])
        >>> nt.is_leaf
        False
        >>> fake_grad = torch.nested.nested_tensor([torch.ones_like(a), torch.zeros_like(b)])
        >>> nt.backward(fake_grad)
        >>> a.grad
        tensor([1., 1., 1.])
        >>> b.grad
        tensor([0., 0., 0., 0., 0.])
        >>> c = torch.randn(3, 5, requires_grad=True)
        >>> nt2 = torch.nested.as_nested_tensor(c)
    """
    is_tensor_list = isinstance(ts, (list, tuple)) and all(
        isinstance(t, Tensor) for t in ts
    )
    if not isinstance(ts, Tensor) and not is_tensor_list:
        raise TypeError(
            "as_nested_tensor(): Expected first argument to be a tensor or a list / tuple of tensors "
        )
    # convert tuple -> list if needed
    if is_tensor_list and not isinstance(ts, list):
        ts = list(ts)

    if isinstance(ts, Tensor) and ts.dim() < 2:
        raise RuntimeError(
            "as_nested_tensor(): Expected tensor argument to have dim() > 1"
        )

    if isinstance(ts, Tensor) and ts.is_nested:
        if layout == ts.layout:
            # return input directly or input copied to device / dtype
            return ts.to(device=device, dtype=dtype)
        else:
            # TODO: Just use nt.to(layout=layout) when it exists.
            raise RuntimeError(
                "as_nested_tensor(): Converting between nested tensor layouts is not supported"
            )

    if layout is None:
        layout = torch.strided
    if layout == torch.strided:
        if isinstance(ts, Tensor):
            # contiguous() might be necessary to get flattened view.
            # we could probably be more precise about when to do this as an optimization
            buffer = ts.contiguous().view(-1).to(device=device, dtype=dtype)
            nested_sizes = torch.tensor([t.shape for t in ts])
            return torch._nested_view_from_buffer(
                buffer,
                nested_sizes,
                *torch._nested_compute_contiguous_strides_offsets(nested_sizes),
            )
        else:
            if not isinstance(ts, list):
                raise AssertionError(
                    f"Expected ts to be a list, but got {type(ts).__name__}"
                )
            return torch._nested_tensor_from_tensor_list(ts, dtype, None, device, None)
    elif layout == torch.jagged:
        if isinstance(ts, Tensor):
            if device is None:
                device = ts.device

            # contiguous() might be necessary to get flattened view.
            # we could probably be more precise about when to do this as an optimization
            values = ts.contiguous().flatten(0, 1).to(device=device, dtype=dtype)
            batch_size = ts.shape[0]
            seq_len = ts.shape[1]
            offsets = torch.arange(
                0, batch_size * seq_len + 1, seq_len, device=device, dtype=torch.int64
            )

            from torch.nested._internal.nested_tensor import (
                nested_view_from_values_offsets,
            )

            return nested_view_from_values_offsets(
                values, offsets, min_seqlen=seq_len, max_seqlen=seq_len
            )
        else:
            from torch.nested._internal.nested_tensor import jagged_from_list

            if not isinstance(ts, list):
                raise AssertionError(
                    f"Expected ts to be a list, but got {type(ts).__name__}"
                )
            nt, _ = jagged_from_list(ts, offsets=None, device=device, dtype=dtype)
            return nt
    else:
        raise RuntimeError(
            f"Specified layout is unsupported for nested tensors: {layout}"
        )