def setitem(self: Any, index: Any, rhs: Any) -> None:
    """Set values in tensor using first-class dimensions."""
    from . import DimensionBindError, TensorInfo

    iinfo = getsetitem(self, index, has_dims(self) or has_dims(rhs))

    if iinfo.can_call_original:
        # Call original tensor __setitem__ directly, bypassing __torch_function__
        torch._C.TensorBase.__setitem__(self, index, rhs)
        return

    # Handle RHS tensor with dimensions
    rhs_info = TensorInfo.create(rhs, False, False)

    if rhs_info:
        # Check that rhs dimensions are compatible with result dimensions
        for l in rhs_info.levels:
            if not l.is_positional():
                # Find this dimension in result levels
                found = False
                for result_level in iinfo.result_levels:
                    if (
                        not result_level.is_positional()
                        and result_level.dim() is l.dim()
                    ):
                        found = True
                        break

                if not found:
                    # Create tuple representation of result levels for error message
                    result_dims: list[int | Dim] = []
                    for rl in iinfo.result_levels:
                        if rl.is_positional():
                            result_dims.append(rl.position())
                        else:
                            result_dims.append(rl.dim())

                    raise DimensionBindError(
                        f"rhs of setitem contains dimension {l.dim()!r} which is not in the dimension on the left "
                        f"({tuple(result_dims)!r})"
                    )

        # Match RHS tensor to result levels
        if rhs_info.tensor is None:
            raise AssertionError("Cannot match levels on None tensor")
        matched_rhs = _match_levels(
            rhs_info.tensor, rhs_info.levels, iinfo.result_levels
        )
    else:
        matched_rhs = rhs

    # For advanced indexing with dimensions, we need special handling
    if iinfo.advanced_indexing:
        # Use advanced indexing - the flat_inputs already contain matched tensors
        tup = slice_to_tuple(iinfo.flat_inputs)
        if iinfo.self_tensor is None:
            raise RuntimeError("Cannot setitem on None tensor")
        torch._C.TensorBase.__setitem__(iinfo.self_tensor, tup, matched_rhs)
    else:
        # Simple copy operation
        if iinfo.self_tensor is None:
            raise RuntimeError("Cannot copy to None tensor")
        iinfo.self_tensor.copy_(matched_rhs)