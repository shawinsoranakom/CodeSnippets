def _get_ignored_buffer_names(
    root_module: torch.nn.Module,
    ignored_modules: set[torch.nn.Module],
) -> set[str]:
    """Return the cleaned buffer FQNs in ``ignored_modules``."""
    all_ignored_buffer_names: set[str] = set()

    buffers_in_ignored_modules = {
        buffer for m in ignored_modules for buffer in m.buffers()
    }

    all_ignored_buffer_names.update(
        {
            clean_tensor_name(buffer_name)
            for buffer_name, buffer in root_module.named_buffers()
            if buffer in buffers_in_ignored_modules
        }
    )

    # Always include nested FSDP modules' ignored buffer names
    for submodule in root_module.modules():
        optional_fsdp_state = _get_module_fsdp_state(submodule)
        if optional_fsdp_state is not None:
            if not hasattr(optional_fsdp_state, "_ignored_buffer_names"):
                raise AssertionError(
                    "Expected optional_fsdp_state to have _ignored_buffer_names attribute"
                )
            all_ignored_buffer_names.update(optional_fsdp_state._ignored_buffer_names)

    return all_ignored_buffer_names