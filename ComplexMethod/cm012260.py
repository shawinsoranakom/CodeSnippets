def definitely_equal(
    old_sizes: Sequence[torch.SymInt | int],
    new_sizes: Sequence[torch.SymInt | torch.fx.Node | int],
) -> bool:
    """
    Leverage guard_or_true/false to compare if two lists of int/symint are equal.
    Useful to compare sizes, strides etc.

    Can handle -1 in new_sizes which happens in the size arguments of a
    view op. old_sizes is supposed to be the tensor shape and should not
    contain -1.

    new_sizes can contains fx.Node when dynamic shape is enabled. In that
    case new_sizes[i].meta['val'] contains the real torch.SymInt.
    """

    num_neg1 = 0

    if len(old_sizes) != len(new_sizes):
        return False

    for lhs_item, rhs_item in zip(old_sizes, new_sizes):
        if isinstance(rhs_item, torch.fx.Node):
            rhs_item = rhs_item.meta["val"]

        assert isinstance(lhs_item, (int, torch.SymInt)), type(lhs_item)
        assert isinstance(rhs_item, (int, torch.SymInt)), type(rhs_item)

        # It still makes sense to call guard_or_true/false since lhs_item
        # rhs_item are torch.SymInt rather than sympy expressions when
        # dynamic shape is enabled.
        if guard_or_false(lhs_item == rhs_item):
            continue

        if guard_or_true(rhs_item != -1):
            return False

        num_neg1 += 1

        if num_neg1 > 1:
            return False
    return True