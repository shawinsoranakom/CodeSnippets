def _get_ignored_modules(
    root_module: nn.Module,
    _ignored_modules: Iterable[torch.nn.Module] | None,
) -> set[nn.Module]:
    """
    Check that ``_ignored_modules`` is an iterable of ``nn.Module`` s without any FSDP instances.

    Return the modules contained in their module
    subtrees as a :class:`set`. Nested FSDP instances are excluded, but their
    already-computed ignored modules are included.

    ``_ignored_modules`` represents the argument passed by the user to FSDP.
    """
    msg_prefix = "`ignored_modules` should be an iterable of `torch.nn.Module`s "
    try:
        ignored_root_modules = (
            set(_ignored_modules) if _ignored_modules is not None else set()
        )
    except TypeError as e:
        raise TypeError(msg_prefix + f"but got {type(_ignored_modules)}") from e
    for module in ignored_root_modules:
        if not isinstance(module, torch.nn.Module):
            raise TypeError(msg_prefix + f"but got an iterable with {type(module)}")
        if _get_module_fsdp_state(module):
            # TODO: We may relax this by taking the FSDP instance's wrapped
            # module to provide more flexibility to the user.
            raise ValueError("`ignored_modules` should not include FSDP modules")
    # Treat modules that cannot compose with `fully_shard` as ignored modules,
    # meaning that their subtrees are ignored
    for module in root_module.modules():
        if not traversal_utils._composable(module):
            ignored_root_modules.add(module)
    # NOTE: Even if `ignored_root_modules` is empty, do not return early so
    # that this FSDP instance can get any ignored modules from its children.

    # Include child modules and exclude nested FSDP modules themselves
    ignored_modules = {
        child
        for module in ignored_root_modules
        for child in module.modules()
        if not isinstance(child, fsdp_file.FullyShardedDataParallel)
    }
    if root_module in ignored_modules:
        warnings.warn(
            "Trying to ignore the top-level module passed into the FSDP "
            "constructor itself will result in all parameters being "
            f"ignored and is not well-supported: {module}",
            stacklevel=2,
        )
    # Include nested FSDP modules' ignored modules
    for submodule in root_module.modules():
        optional_fsdp_state = _get_module_fsdp_state(submodule)
        if optional_fsdp_state is not None:
            if not hasattr(optional_fsdp_state, "_ignored_modules"):
                raise AssertionError(
                    "Expected optional_fsdp_state to have _ignored_modules attribute"
                )
            ignored_modules.update(optional_fsdp_state._ignored_modules)
    return ignored_modules