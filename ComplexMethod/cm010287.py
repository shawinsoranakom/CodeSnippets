def _get_param_buffer_mapping(
    original_module: torch.nn.Module,
    traced_module: torch.nn.Module,
) -> dict[str, str]:
    """
    Returns a mapping of parameter/buffer names from the new module to the
    original model. This is to help with restoring the FQN for parameter/buffers
    of a traced module to what the original module contains.
    """

    param_lookup: dict[int, str] = {}
    buffer_lookup: dict[int, str] = {}
    for name, param in original_module.named_parameters(remove_duplicate=False):
        if param_lookup.get(id(param)) is None:
            # we only want to keep the first occurrence of a parameter to guarantee parity of original and traced module.
            param_lookup[id(param)] = name
    for name, buffer in original_module.named_buffers(remove_duplicate=False):
        buffer_lookup[id(buffer)] = name

    param_buffer_table: dict[str, str] = {}
    for dynamo_name, dynamo_param in traced_module.named_parameters(
        remove_duplicate=False
    ):
        if dynamo_name in param_buffer_table:
            raise AssertionError(
                f"dynamo_name {dynamo_name!r} already exists in param_buffer_table"
            )
        if id(dynamo_param) in param_lookup:
            param_buffer_table[dynamo_name] = param_lookup[id(dynamo_param)]

    for dynamo_name, dynamo_buffer in traced_module.named_buffers(
        remove_duplicate=False
    ):
        if dynamo_name in param_buffer_table:
            raise AssertionError(
                f"dynamo_name {dynamo_name!r} already exists in param_buffer_table for buffer"
            )
        if id(dynamo_buffer) in buffer_lookup:
            param_buffer_table[dynamo_name] = buffer_lookup[id(dynamo_buffer)]

    return param_buffer_table