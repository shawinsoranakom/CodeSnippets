def has_fake_kernel(op: torch._ops.OpOverload) -> bool:
    """If an operator (that stays alive until FakeTensorMode) has a Fake kernel.
    Don't use this if the operator decomposes before FakeTensorMode.
    """
    if can_generate_trivial_fake_impl(op):
        return True
    name = op._name
    if torch._C._dispatch_has_kernel_for_dispatch_key(
        name, "CompositeImplicitAutograd"
    ):
        return True
    opdef = torch._library.custom_ops._maybe_get_opdef(name)
    if opdef is None:
        # the non-torch.library.custom_op path
        if torch._C._dispatch_has_kernel_for_dispatch_key(
            name, "CompositeExplicitAutograd"
        ):
            return True
        entry = torch._library.simple_registry.singleton.find(name)
        if entry.fake_impl.kernel is not None:
            return True
        if torch._C._dispatch_has_kernel_for_dispatch_key(name, "Meta"):
            return True
    else:
        # the torch.library.custom_op path
        if opdef._abstract_fn is not None:
            return True
    return False