def cat(
    tensors: list[torch.Tensor],
    dim: int = 0,
) -> torch.Tensor:
    def non_empty_tensor(x: torch.Tensor) -> bool:
        # For better or worse, this is a valid cat:
        #
        #   torch.cat([torch.randn(2, 2, 4), torch.randn(0), torch.randn(3, 2, 4)])
        #
        # We'd like to eliminate naughtiness like this for downstream passes
        # like split_cat.  The easiest way is to just drop such inputs
        # (guarding that they are non-zero).
        #
        # Is it permissible for this filtering to be size-oblivious?  A case
        # where this could matter is cat([(2, 2), (u0,)], dim=0); if u0
        # happened to be zero, we would have liked to have filtered it out.
        # But actually, the ONLY way this could have passed is if u0 == 0,
        # so by the time we get here we have already installed a deferred
        # runtime assert forcing u0 to be zero.  So if this hasn't happened,
        # we know that the unbacked SymInt has appropriate size and there are
        # no problems.
        if len(x.shape) == 1 and guard_or_false(x.shape[0] == 0):
            return False

        if dim < len(x.shape) and guard_or_false(x.shape[dim] == 0):
            return False

        return True

    filtered_tensors = list(filter(non_empty_tensor, tensors))

    if len(filtered_tensors) == 1:
        # check dtype promotion
        promoted_dtype = elementwise_dtypes(
            *tensors,
            type_promotion_kind=ELEMENTWISE_TYPE_PROMOTION_KIND.DEFAULT,
        )[1]
        filtered_t = filtered_tensors[0]
        return (
            filtered_t.clone()
            if promoted_dtype == filtered_t.dtype
            else filtered_t.to(dtype=promoted_dtype)
        )
    elif 1 < len(filtered_tensors) < len(tensors):
        # on the first call, when we remove empty tensors, we redispatch recursively
        return aten.cat.default(filtered_tensors, dim)

    # optimization, avoid concat for single, repeated input
    if len(filtered_tensors) > 1 and all(
        t is filtered_tensors[0] for t in filtered_tensors
    ):
        inp = filtered_tensors[0]
        shape = list(inp.shape)
        dim = dim + len(inp.shape) if dim < 0 else dim
        shape.insert(dim, len(filtered_tensors))
        return inp.unsqueeze(dim).expand(*shape).flatten(dim, dim + 1).clone()

    # when no 'filtering' has occurred, we raise to prevent infinite recursion (no more decomposition needed)
    return NotImplemented