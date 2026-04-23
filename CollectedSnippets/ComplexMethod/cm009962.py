def getsetitem(self: Any, index: Any, tensors_have_dims: bool) -> IndexingInfo:
    from . import DimList  # Import DimList for type checking

    can_call_original_getitem = not tensors_have_dims

    input_list = []
    if has_dims(index):
        input_list.append(index)
    else:
        is_sequence = extractIndices(index, input_list)
        # nothing about first class dims here, fallback to getitem
        if can_call_original_getitem and not is_sequence:
            return IndexingInfo(can_call_original=True)

    # Calculate how many dimensions have been indexed in order to compute the
    # size of ... or expand a potentially unbound dimension list.
    dims_indexed = 0
    expanding_object = -1
    unbound_dim_list = None
    dimlists = []  # Track DimList positions for later processing

    def check_expanding(i: int) -> None:
        nonlocal expanding_object
        if expanding_object != -1:
            from . import DimensionBindError

            raise DimensionBindError(
                f"at most one ... or unbound dimension list can exist in indexing list but found 2 at offsets "
                f"{expanding_object} and {i}"
            )
        expanding_object = i

    def is_dimpack(s: Any) -> bool:
        from . import Dim

        return (
            isinstance(s, (tuple, list))
            and len(s) > 0
            and all(Dim.check_exact(item) for item in s)
        )

    has_dimpacks_or_none = False
    for i, s in enumerate(input_list):
        if has_dims(s):
            can_call_original_getitem = False
            dims_indexed += 1
        elif s is ...:
            check_expanding(i)
        elif isinstance(s, DimList):
            can_call_original_getitem = False
            if not s.is_bound:
                check_expanding(i)
                unbound_dim_list = s
            else:
                dims_indexed += len(s._dims)
            dimlists.append(i)
        elif s is None:
            has_dimpacks_or_none = True
        elif is_dimpack(s):
            can_call_original_getitem = False
            has_dimpacks_or_none = True
            dims_indexed += 1
        else:
            dims_indexed += 1

    # Early return if we can use original getitem
    if can_call_original_getitem:
        return IndexingInfo(can_call_original=True)

    self_info = TensorInfo.create(self, False, True)
    total_dims = len(self_info.levels)  # Total dimensions (positional + named)
    if dims_indexed > total_dims:
        raise ValueError(
            f"at least {dims_indexed} indices were supplied but the tensor only has {total_dims} dimensions"
        )

    # Expand any unbound dimension list, or expand ... into individual : slices.
    expanding_dims = total_dims - dims_indexed
    if expanding_object != -1:
        if unbound_dim_list is not None:
            # Bind unbound dimension list to the expanding dimensions
            unbound_dim_list.bind_len(expanding_dims)
        else:
            # Expand ... into slice(None) objects
            no_slices = [slice(None)] * expanding_dims
            input_list = (
                input_list[:expanding_object]
                + no_slices
                + input_list[expanding_object + 1 :]
            )

    # Flatten out any dimensions stored in dimlist elements directly into the inputs
    # Process in reverse order to maintain indices
    for i in range(len(dimlists) - 1, -1, -1):
        idx = dimlists[i]

        # We added more elements to input because of ...
        # so we need to also adjust the index to get back to where the
        # dimlist existed
        if (
            unbound_dim_list is None
            and expanding_object != -1
            and idx > expanding_object
        ):
            idx += expanding_dims

        dl = input_list[idx]

        # PRIVATE here naughty
        input_list = input_list[:idx] + dl._dims + input_list[idx + 1 :]

    return getsetitem_flat(self_info, input_list, [], [], has_dimpacks_or_none)