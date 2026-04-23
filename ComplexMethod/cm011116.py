def _need_to_materialize_module(
    module: nn.Module,
    ignored_params: set[nn.Parameter],
    ignored_modules: set[nn.Module],
) -> tuple[bool, bool]:
    """
    Return if ``module`` has parameters on meta device and if ``module`` is using torchdistX deferred initialization.

    At most of the returned bools can
    be ``True``. If either is ``True``, then ``module`` needs to be
    materialized.
    """
    managed_params = list(_get_orig_params(module, ignored_params))
    is_meta_module = any(param.is_meta for param in managed_params)
    # TODO: We need to establish a contract for FSDP and buffers. For now, we
    # skip checking for meta buffers from ignored modules. We should consider
    # refactoring the initialization holistically to avoid so many traversals.
    for submodule in module.modules():
        if submodule in ignored_modules:
            continue
        for buf in submodule.buffers(recurse=False):
            is_meta_module |= buf.is_meta
    is_torchdistX_deferred_init = (
        not is_meta_module
        and _TORCHDISTX_AVAIL
        and any(fake.is_fake(param) for param in managed_params)
    )
    return is_meta_module, is_torchdistX_deferred_init