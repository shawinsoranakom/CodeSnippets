def check_value(
    value: ZwaveValue,
    schema: ZWaveValueDiscoverySchema,
    primary_value: ZwaveValue | None = None,
) -> bool:
    """Check if value matches scheme."""
    # check command_class
    if (
        schema.command_class is not None
        and value.command_class not in schema.command_class
    ):
        return False
    # check endpoint
    if schema.endpoint is not None and value.endpoint not in schema.endpoint:
        return False
    # If the schema does not require an endpoint, make sure the value is on the
    # same endpoint as the primary value
    if (
        schema.endpoint is None
        and primary_value is not None
        and value.endpoint != primary_value.endpoint
    ):
        return False
    # check property
    if schema.property is not None and value.property_ not in schema.property:
        return False
    # check property_name
    if (
        schema.property_name is not None
        and value.property_name not in schema.property_name
    ):
        return False
    # check property_key
    if (
        schema.property_key is not None
        and value.property_key not in schema.property_key
    ):
        return False
    # check property_key against not_property_key set
    if (
        schema.not_property_key is not None
        and value.property_key in schema.not_property_key
    ):
        return False
    # check metadata_type
    if schema.type is not None and value.metadata.type not in schema.type:
        return False
    # check metadata_readable
    if schema.readable is not None and value.metadata.readable != schema.readable:
        return False
    # check metadata_writeable
    if schema.writeable is not None and value.metadata.writeable != schema.writeable:
        return False
    # check available states
    if (
        schema.any_available_states is not None
        and value.metadata.states is not None
        and not any(
            str(key) in value.metadata.states and value.metadata.states[str(key)] == val
            for key, val in schema.any_available_states
        )
    ):
        return False
    if (
        schema.any_available_states_keys is not None
        and value.metadata.states is not None
        and not any(
            str(key) in value.metadata.states
            for key in schema.any_available_states_keys
        )
    ):
        return False
    # check available cc specific
    if schema.all_available_cc_specific is not None and (
        value.metadata.cc_specific is None
        or not all(
            key in value.metadata.cc_specific and value.metadata.cc_specific[key] == val
            for key, val in schema.all_available_cc_specific
        )
    ):
        return False
    if schema.any_available_cc_specific is not None and (
        value.metadata.cc_specific is None
        or not any(
            key in value.metadata.cc_specific and value.metadata.cc_specific[key] == val
            for key, val in schema.any_available_cc_specific
        )
    ):
        return False
    # check value
    if schema.value is not None and value.value not in schema.value:
        return False
    # check metadata_stateful
    if schema.stateful is not None and value.metadata.stateful != schema.stateful:
        return False
    return True