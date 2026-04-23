def condenser_config_from_toml_section(
    data: dict, llm_configs: dict | None = None
) -> dict[str, CondenserConfig]:
    """Create a CondenserConfig instance from a toml dictionary representing the [condenser] section.

    For CondenserConfig, the handling is different since it's a union type. The type of condenser
    is determined by the 'type' field in the section.

    Example:
    Parse condenser config like:
        [condenser]
        type = "noop"

    For condensers that require an LLM config, you can specify the name of an LLM config:
        [condenser]
        type = "llm"
        llm_config = "my_llm"  # References [llm.my_llm] section

    Args:
        data: The TOML dictionary representing the [condenser] section.
        llm_configs: Optional dictionary of LLMConfig objects keyed by name.

    Returns:
        dict[str, CondenserConfig]: A mapping where the key "condenser" corresponds to the configuration.
    """
    # Initialize the result mapping
    condenser_mapping: dict[str, CondenserConfig] = {}

    # Process config
    try:
        # Determine which condenser type to use based on 'type' field
        condenser_type = data.get('type', 'noop')

        # Handle LLM config reference if needed
        if (
            condenser_type in ('llm', 'llm_attention')
            and 'llm_config' in data
            and isinstance(data['llm_config'], str)
        ):
            llm_config_name = data['llm_config']
            if llm_configs and llm_config_name in llm_configs:
                # Replace the string reference with the actual LLMConfig object
                data_copy = data.copy()
                data_copy['llm_config'] = llm_configs[llm_config_name]
                config = create_condenser_config(condenser_type, data_copy)
            else:
                logger.openhands_logger.warning(
                    f"LLM config '{llm_config_name}' not found for condenser. Using default LLMConfig."
                )
                # Create a default LLMConfig if the referenced one doesn't exist
                data_copy = data.copy()
                # Try to use the fallback 'llm' config
                if llm_configs is not None:
                    data_copy['llm_config'] = llm_configs.get('llm')
                config = create_condenser_config(condenser_type, data_copy)
        else:
            config = create_condenser_config(condenser_type, data)

        condenser_mapping['condenser'] = config
    except (ValidationError, ValueError) as e:
        logger.openhands_logger.warning(
            f'Invalid condenser configuration: {e}. Using NoOpCondenserConfig.'
        )
        # Default to NoOpCondenserConfig if config fails
        config = NoOpCondenserConfig(type='noop')
        condenser_mapping['condenser'] = config

    return condenser_mapping