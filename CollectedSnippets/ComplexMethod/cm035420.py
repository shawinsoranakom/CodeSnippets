def get_condenser_config_arg(
    condenser_config_arg: str, toml_file: str = 'config.toml'
) -> CondenserConfig | None:
    """Get a group of condenser settings from the config file by name.

    A group in config.toml can look like this:

    ```
    [condenser.my_summarizer]
    type = 'llm'
    llm_config = 'gpt-4o' # References [llm.gpt-4o]
    max_size = 50
    ...
    ```

    The user-defined group name, like "my_summarizer", is the argument to this function.
    The function will load the CondenserConfig object with the settings of this group,
    from the config file.

    Note that the group must be under the "condenser" group, or in other words,
    the group name must start with "condenser.".

    Args:
        condenser_config_arg: The group of condenser settings to get from the config.toml file.
        toml_file: Path to the configuration file to read from. Defaults to 'config.toml'.

    Returns:
        CondenserConfig: The CondenserConfig object with the settings from the config file, or None if not found/error.
    """
    # keep only the name, just in case
    condenser_config_arg = condenser_config_arg.strip('[]')

    # truncate the prefix, just in case
    if condenser_config_arg.startswith('condenser.'):
        condenser_config_arg = condenser_config_arg[10:]

    logger.openhands_logger.debug(
        f'Loading condenser config [{condenser_config_arg}] from {toml_file}'
    )

    # load the toml file
    try:
        with open(toml_file, 'r', encoding='utf-8') as toml_contents:
            toml_config = toml.load(toml_contents)
    except FileNotFoundError as e:
        logger.openhands_logger.info(f'Config file not found: {toml_file}. Error: {e}')
        return None
    except toml.TomlDecodeError as e:
        logger.openhands_logger.error(
            f'Cannot parse condenser group [{condenser_config_arg}] from {toml_file}. Exception: {e}'
        )
        return None

    # Check if the condenser section and the specific config exist
    if (
        'condenser' not in toml_config
        or condenser_config_arg not in toml_config['condenser']
    ):
        logger.openhands_logger.error(
            f'Condenser config section [condenser.{condenser_config_arg}] not found in {toml_file}'
        )
        return None

    condenser_data = toml_config['condenser'][
        condenser_config_arg
    ].copy()  # Use copy to modify

    # Determine the type and handle potential LLM dependency
    condenser_type = condenser_data.get('type')
    if not condenser_type:
        logger.openhands_logger.error(
            f'Missing "type" field in [condenser.{condenser_config_arg}] section of {toml_file}'
        )
        return None

    # Handle LLM config reference if needed, using get_llm_config_arg
    if (
        condenser_type in ('llm', 'llm_attention', 'structured')
        and 'llm_config' in condenser_data
        and isinstance(condenser_data['llm_config'], str)
    ):
        llm_config_name = condenser_data['llm_config']
        logger.openhands_logger.debug(
            f'Condenser [{condenser_config_arg}] requires LLM config [{llm_config_name}]. Loading it...'
        )
        # Use the existing function to load the specific LLM config
        referenced_llm_config = get_llm_config_arg(llm_config_name, toml_file=toml_file)

        if referenced_llm_config:
            # Replace the string reference with the actual LLMConfig object
            condenser_data['llm_config'] = referenced_llm_config
        else:
            # get_llm_config_arg already logs the error if not found
            logger.openhands_logger.error(
                f"Failed to load required LLM config '{llm_config_name}' for condenser '{condenser_config_arg}'."
            )
            return None

    # Create the condenser config instance
    try:
        config = create_condenser_config(condenser_type, condenser_data)
        logger.openhands_logger.info(
            f'Successfully loaded condenser config [{condenser_config_arg}] from {toml_file}'
        )
        return config
    except (ValidationError, ValueError) as e:
        logger.openhands_logger.error(
            f'Invalid condenser configuration for [{condenser_config_arg}]: {e}.'
        )
        return None