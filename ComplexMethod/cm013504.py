def check_consistent(new: _T, old: _T) -> None:
    """
    Test that two "meta" values (typically either Tensor or SymInt) have
    the same values, e.g., after retracing.  If we don't understand the
    quantities in question, we'll just skip the consistency check.
    """
    # TODO: do boolean equality test too, see
    # https://github.com/pytorch/pytorch/issues/124110
    scalar_types = (torch.SymInt, torch.SymFloat, int, float)

    if isinstance(new, torch.Tensor):
        if not isinstance(old, torch.Tensor):
            raise AssertionError(f"Expected Tensor, got {type(old)}")
        torch._check(
            old.dim() == new.dim(), lambda: f"{old.shape} != {new.shape} (old != new)"
        )
        # Do this manually so that each individual test is irrefutable
        # (TODO: should be a helper for this, maybe sym_eq?  That
        # gives us a compound expression and I'm not sure it
        # simplifies right now)
        for i, j in zip(old.shape, new.shape):
            torch._check(i == j, lambda: f"{old.shape} != {new.shape} (old != new)")
    # NB: bool is subclass of int
    elif isinstance(new, scalar_types) and not isinstance(new, bool):
        if not (isinstance(old, scalar_types) and not isinstance(old, bool)):
            raise AssertionError(f"{old} != {new}")
        torch._check(old == new, lambda: f"{old} != {new} (old != new)")