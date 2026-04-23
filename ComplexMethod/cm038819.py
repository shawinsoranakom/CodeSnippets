def is_in_target_modules(
    module_name: str,
    target_modules: list[str] | None,
    packed_modules_mapping: dict[str, list[str]] | None = None,
) -> bool:
    """Check if a module passes the deployment-time target_modules filter.

    When target_modules is None (no restriction), all modules pass.
    Otherwise, the module's suffix must be in the target_modules list.

    Args:
        module_name: Full dot-separated module name.
        target_modules: Optional deployment-time restriction list from
            LoRAConfig.target_modules.
        packed_modules_mapping: Optional model-defined mapping from packed
            runtime module names to their adapter-visible submodule names
            (e.g. ``{"gate_up_proj": ["gate_proj", "up_proj"]}``).

    Returns:
        True if the module passes the filter, False otherwise.
    """
    if target_modules is None:
        return True
    target_module_set = set(target_modules)
    module_suffix = module_name.split(".")[-1]
    if module_suffix in target_module_set or module_name in target_module_set:
        return True

    if not packed_modules_mapping:
        return False

    # Runtime packed parent matched by deployment-time child targets.
    packed_children = packed_modules_mapping.get(module_suffix)
    if packed_children and any(child in target_module_set for child in packed_children):
        return True

    # Adapter-visible packed child matched by deployment-time parent target.
    return any(
        module_suffix in children and packed_parent in target_module_set
        for packed_parent, children in packed_modules_mapping.items()
    )