def use_triton_tma_template(
    *matrices: IRNode, output_layout: Layout, add_guards: bool = False
) -> bool:
    if not config.triton.enable_persistent_tma_matmul:
        return False
    if not all(len(m.get_size()) == 2 for m in matrices):
        return False
    if not all(
        _descriptor_shape_fits_in_int32(m.get_size(), add_guards=add_guards)
        for m in matrices
    ):
        return False
    if config.triton.enable_template_tma_store and not _descriptor_shape_fits_in_int32(
        output_layout.size, add_guards=add_guards
    ):
        return False
    # On AMD (HIP), TMA is not available but we still use non-TMA persistent
    # kernels, so skip the TMA compatibility checks.
    if torch.version.hip is not None:
        return True
    layout = output_layout if config.triton.enable_template_tma_store else None
    return can_use_tma(*matrices, output_layout=layout, add_guards=add_guards)