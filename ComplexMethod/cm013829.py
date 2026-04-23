def _binary_helper(fn, args, kwargs, inplace):
    if len(kwargs) != 0:
        raise ValueError("len(kwargs) must equal 0")
    for a in args[2:]:
        if torch.is_tensor(a):
            raise TypeError(
                "MaskedTensor binary ops do not support Tensor arguments aside from the lhs and rhs"
            )

    if not _masks_match(*args[:2]):
        raise ValueError(
            "Input masks must match. If you need support for this, please open an issue on Github."
        )

    data_args, _data_kwargs = _map_mt_args_kwargs(args, kwargs, lambda x: x.get_data())
    mask_args, _mask_kwargs = _map_mt_args_kwargs(args, kwargs, lambda x: x.get_mask())

    args0_layout = data_args[0].layout
    same_layout = (
        torch.is_tensor(data_args[1]) or is_masked_tensor(data_args[1])
    ) and (args0_layout == data_args[1].layout)

    if args0_layout == torch.sparse_coo:
        if same_layout:
            if not _tensors_match(data_args[0].indices(), data_args[1].indices()):
                raise ValueError(
                    "sparse_coo indices must match. If you need support for this, please open an issue on Github."
                )
            if data_args[0].size() != data_args[1].size():
                raise ValueError(
                    "input1 and input2 must have the same size for binary functions."
                )

            data_args[1] = data_args[1].values()

        i = data_args[0].indices()
        size = data_args[0].size()
        data_args[0] = data_args[0].values()
        v = fn(*data_args)
        result_data = torch.sparse_coo_tensor(i, v, size)

    elif args0_layout == torch.sparse_csr:
        if same_layout:
            if not (
                _tensors_match(data_args[0].crow_indices(), data_args[1].crow_indices())
                and _tensors_match(
                    data_args[0].col_indices(), data_args[1].col_indices()
                )
            ):
                raise ValueError(
                    "sparse_csr indices must match. If you need support for this, please open an issue on Github."
                )

            data_args[1] = data_args[1].values()

        crow = data_args[0].crow_indices()
        col = data_args[0].col_indices()
        size = data_args[0].size()
        data_args[0] = data_args[0].values()
        v = fn(*data_args)
        result_data = torch.sparse_csr_tensor(crow, col, v, size)

    else:
        result_data = fn(*data_args)

    if inplace:
        args[0]._set_data_mask(result_data, mask_args[0])
        return args[0]
    else:
        result_mask = _get_at_least_one_mask(*args[:2])
        # sparse tensors don't have strides so we can only expand if the layout is strided
        if args0_layout == torch.strided:
            result_mask = result_mask.expand_as(result_data)
        return _wrap_result(result_data, result_mask)