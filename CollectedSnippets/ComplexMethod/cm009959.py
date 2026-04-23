def _bind_dims_to_size(sz: int, sd: int, dims: list, nsz: list, nsd: list) -> None:
    """
    Bind dimensions to size and calculate proper strides for dim packs.
    """
    from . import DimensionBindError

    rhs_prod = 1
    for i, dim in enumerate(dims):
        if not dim.is_bound:
            # Check for multiple unbound dimensions
            for j in range(i + 1, len(dims)):
                if not dims[j].is_bound:
                    raise DimensionBindError(
                        f"cannot infer the sizes of two dimensions at once {dim!r} and {dims[j]!r}"
                    )
                rhs_prod *= dims[j].size

            # Calculate the size for this unbound dimension
            if sz % rhs_prod != 0:
                tup = tuple(dim.size if dim.is_bound else "?" for dim in dims)
                raise DimensionBindError(
                    f"inferred dimension does not evenly fit into larger dimension: {sz} vs {tup}"
                )

            inferred_size = sz // rhs_prod
            dim.size = inferred_size
            rhs_prod = sz
            break
        else:
            rhs_prod *= dim.size

    # Final validation that dimensions match
    if rhs_prod != sz:
        tup = tuple(dims)
        raise DimensionBindError(
            f"Dimension sizes to do not match ({sz} != {rhs_prod}) when matching dimension pack {tup}"
        )

    # Calculate new sizes and strides for each dimension in the pack
    # First calculate all strides by iterating in reverse
    new_strides = [0] * len(dims)
    current_stride = sd
    for i in reversed(range(len(dims))):
        new_strides[i] = current_stride
        current_stride *= dims[i].size

    # Then append sizes and strides in forward order
    for i in range(len(dims)):
        nsz.append(dims[i].size)
        nsd.append(new_strides[i])