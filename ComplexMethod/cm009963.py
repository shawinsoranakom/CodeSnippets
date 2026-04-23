def getsetitem_flat(
    self_info: TensorInfo,
    input_list: list,
    keys: list[DimEntry],
    values: list,
    has_dimpacks_or_none: bool,
) -> IndexingInfo:
    from . import Dim

    # Track dimension usage
    seen_dims: list[Any] = []
    seen_dims_nuses: list[int] = []

    def add_dim(dim: Any) -> None:
        # Use safe indexing to avoid triggering __torch_function__ on Dim objects
        idx = _safe_index(seen_dims, dim)
        if idx is not None:
            seen_dims_nuses[idx] += 1
        else:
            seen_dims.append(dim)
            seen_dims_nuses.append(1)

    flat_inputs = []
    tensor_inputs: list[Any] = []
    device_holding_tensor = None

    def append_flat_handle(handle: Any) -> None:
        flat_inputs.append(handle)
        tensor_inputs.append(None)

    def append_tensor_input(ti: TensorInfo) -> None:
        flat_inputs.append(None)
        tensor_inputs.append(ti)
        nonlocal device_holding_tensor
        if ti.has_device and device_holding_tensor is None:
            device_holding_tensor = ti.tensor

    nsz = []
    nsd = []
    if self_info.tensor is None:
        raise RuntimeError("Cannot get size/stride on None tensor")
    sz = self_info.tensor.size()
    sd = self_info.tensor.stride()

    def append_size(i: int) -> None:
        if has_dimpacks_or_none:
            nsz.append(sz[i])
            nsd.append(sd[i])

    input_it = input_list[:]

    def parse_nones() -> None:
        nonlocal input_it
        while input_it and input_it[0] is None:
            append_flat_handle(slice(None))
            nsz.append(1)
            nsd.append(0)
            input_it = input_it[1:]

    def append_item(i: int, arg: Any) -> None:
        if Dim.check_exact(arg):
            d = arg
            if d._size == -1:
                d.size = sz[i]
            add_dim(d)
            append_size(i)
            append_flat_handle(arg)
            return

        info = TensorInfo.create(arg, False, False)
        if info:
            append_size(i)
            append_tensor_input(info)
            for level in info.levels:
                if not level.is_positional():
                    add_dim(level.dim())
            return

        if has_dimpacks_or_none:
            if isinstance(arg, (tuple, list)) and all(Dim.check_exact(d) for d in arg):
                # dim pack
                dim_pack = list(arg)
                for d in dim_pack:
                    add_dim(d)
                    append_flat_handle(d)
                _bind_dims_to_size(sz[i], sd[i], dim_pack, nsz, nsd)
                return

        append_size(i)
        append_flat_handle(arg)

    # Match indexing expressions with tensor dimensions
    for i, level in enumerate(self_info.levels):
        # Use safe indexing to avoid triggering __torch_function__ on DimEntry comparisons
        idx = _safe_index(keys, level)
        if idx is not None:
            append_item(i, values[idx])
        else:
            if level.is_positional():
                parse_nones()
                if not input_it:
                    append_flat_handle(slice(None))
                    append_size(i)
                else:
                    arg = input_it[0]
                    input_it = input_it[1:]
                    append_item(i, arg)
            else:
                add_dim(level.dim())
                append_flat_handle(level.dim())
                append_size(i)

    parse_nones()

    # Restride tensor if needed
    if has_dimpacks_or_none and nsz:
        if self_info.tensor is None:
            raise RuntimeError("Cannot restride None tensor")
        self_tensor = self_info.tensor.as_strided(
            nsz, nsd, self_info.tensor.storage_offset()
        )
    else:
        self_tensor = self_info.tensor

    # Determine result shape and indexing requirements
    result_levels: list[Any] = []
    index_levels = []
    tensor_insert_point = -1
    requires_getindex = False

    def mark_tensor_index() -> None:
        nonlocal tensor_insert_point
        if tensor_insert_point == -1:
            tensor_insert_point = len(result_levels)
        elif tensor_insert_point != len(result_levels):
            tensor_insert_point = 0

    for i, inp in enumerate(flat_inputs):
        if tensor_inputs[i] is not None:
            requires_getindex = True
            mark_tensor_index()
            for level in tensor_inputs[i].levels:
                if level not in index_levels:
                    index_levels.append(level)
        elif Dim.check_exact(inp):
            d = inp
            # Use safe indexing to avoid triggering __torch_function__
            dim_idx = _safe_index(seen_dims, d)
            if dim_idx is None:
                raise AssertionError(f"Dim {d} not found in seen_dims")
            if seen_dims_nuses[dim_idx] == 1:
                flat_inputs[i] = slice(None)
                result_levels.append(DimEntry(d))
            else:
                requires_getindex = True
                flat_inputs[i] = None
                tensor_inputs[i] = TensorInfo(
                    d._get_range(), [DimEntry(d)], False, None
                )
                if DimEntry(d) not in index_levels:
                    index_levels.append(DimEntry(d))
                mark_tensor_index()
        else:
            if inp != slice(None):
                requires_getindex = True
            if not isinstance(inp, int):
                result_levels.append(DimEntry(-1))

    # Insert indexing dimensions at first tensor use point
    if tensor_insert_point != -1:
        for level in reversed(index_levels):
            result_levels.insert(tensor_insert_point, level)

    # Match tensors to indexing shape
    if requires_getindex:
        for i in range(len(flat_inputs)):
            if tensor_inputs[i] is not None:
                t = tensor_inputs[i].tensor
                if t is None:
                    raise AssertionError("TensorInfo should have valid tensor data")
                if (
                    not tensor_inputs[i].has_device
                    and device_holding_tensor is not None
                ):
                    t = t.to(device_holding_tensor.device)
                flat_inputs[i] = _match_levels(t, tensor_inputs[i].levels, index_levels)

    # Number positional dimensions correctly
    seen_positionals = 0
    for i in reversed(range(len(result_levels))):
        if result_levels[i].is_positional():
            seen_positionals += 1
            result_levels[i] = DimEntry(-seen_positionals)

    return IndexingInfo(
        can_call_original=False,
        advanced_indexing=requires_getindex,
        self_tensor=self_tensor,
        flat_inputs=flat_inputs,
        result_levels=result_levels,
        has_device=self_info.has_device,
    )