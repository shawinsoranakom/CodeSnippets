def load_from_toml(cfg: OpenHandsConfig, toml_file: str = 'config.toml') -> None:
    """Load the config from the toml file. Supports both styles of config vars.

    Args:
        cfg: The OpenHandsConfig object to update attributes of.
        toml_file: The path to the toml file. Defaults to 'config.toml'.

    See Also:
    - config.template.toml for the full list of config options.
    """
    # try to read the config.toml file into the config object
    try:
        with open(toml_file, 'r', encoding='utf-8') as toml_contents:
            toml_config = toml.load(toml_contents)
    except FileNotFoundError as e:
        logger.openhands_logger.info(
            f'{toml_file} not found: {e}. Toml values have not been applied.'
        )
        return
    except toml.TomlDecodeError as e:
        logger.openhands_logger.warning(
            f'Cannot parse config from toml, toml values have not been applied.\nError: {e}',
        )
        return

    # Check for the [core] section
    if 'core' not in toml_config:
        logger.openhands_logger.warning(
            f'No [core] section found in {toml_file}. Core settings will use defaults.'
        )
        core_config = {}
    else:
        core_config = toml_config['core']

    # Process core section if present
    cfg_type_hints = get_type_hints(cfg.__class__)
    for key, value in core_config.items():
        if hasattr(cfg, key):
            # Get expected type of the attribute
            expected_type = cfg_type_hints.get(key, None)

            # Check if expected_type is a Union that includes SecretStr and value is str, e.g. search_api_key
            if expected_type:
                origin = get_origin(expected_type)
                args = get_args(expected_type)

                if origin is UnionType and SecretStr in args and isinstance(value, str):
                    value = SecretStr(value)
                elif expected_type is SecretStr and isinstance(value, str):
                    value = SecretStr(value)

            setattr(cfg, key, value)
        else:
            logger.openhands_logger.warning(
                f'Unknown config key "{key}" in [core] section'
            )

    # Process agent section if present
    if 'agent' in toml_config:
        try:
            agent_mapping = AgentConfig.from_toml_section(toml_config['agent'])
            for agent_key, agent_conf in agent_mapping.items():
                cfg.set_agent_config(agent_conf, agent_key)
        except (TypeError, KeyError, ValidationError) as e:
            logger.openhands_logger.warning(
                f'Cannot parse [agent] config from toml, values have not been applied.\nError: {e}'
            )

    # Process llm section if present
    if 'llm' in toml_config:
        try:
            llm_mapping = LLMConfig.from_toml_section(toml_config['llm'])
            for llm_key, llm_conf in llm_mapping.items():
                cfg.set_llm_config(llm_conf, llm_key)
        except (TypeError, KeyError, ValidationError) as e:
            logger.openhands_logger.warning(
                f'Cannot parse [llm] config from toml, values have not been applied.\nError: {e}'
            )

    # Process security section if present
    if 'security' in toml_config:
        try:
            security_mapping = SecurityConfig.from_toml_section(toml_config['security'])
            # We only use the base security config for now
            if 'security' in security_mapping:
                cfg.security = security_mapping['security']
        except (TypeError, KeyError, ValidationError) as e:
            logger.openhands_logger.warning(
                f'Cannot parse [security] config from toml, values have not been applied.\nError: {e}'
            )
        except ValueError:
            # Re-raise ValueError from SecurityConfig.from_toml_section
            raise ValueError('Error in [security] section in config.toml')

    if 'model_routing' in toml_config:
        try:
            model_routing_mapping = ModelRoutingConfig.from_toml_section(
                toml_config['model_routing']
            )
            # We only use the base model routing config for now
            if 'model_routing' in model_routing_mapping:
                default_agent_config = cfg.get_agent_config()
                default_agent_config.model_routing = model_routing_mapping[
                    'model_routing'
                ]

                # Construct the llms_for_routing by filtering llms with for_routing = True
                llms_for_routing_dict = {}
                for llm_name, llm_config in cfg.llms.items():
                    if llm_config and llm_config.for_routing:
                        llms_for_routing_dict[llm_name] = llm_config
                default_agent_config.model_routing.llms_for_routing = (
                    llms_for_routing_dict
                )

                logger.openhands_logger.debug(
                    'Default model routing configuration loaded from config toml and assigned to default agent'
                )
        except (TypeError, KeyError, ValidationError) as e:
            logger.openhands_logger.warning(
                f'Cannot parse [model_routing] config from toml, values have not been applied.\nError: {e}'
            )

    # Process sandbox section if present
    if 'sandbox' in toml_config:
        try:
            sandbox_mapping = SandboxConfig.from_toml_section(toml_config['sandbox'])
            # We only use the base sandbox config for now
            if 'sandbox' in sandbox_mapping:
                cfg.sandbox = sandbox_mapping['sandbox']
        except (TypeError, KeyError, ValidationError) as e:
            logger.openhands_logger.warning(
                f'Cannot parse [sandbox] config from toml, values have not been applied.\nError: {e}'
            )
        except ValueError as e:
            # Re-raise ValueError from SandboxConfig.from_toml_section
            raise ValueError('Error in [sandbox] section in config.toml') from e

    # Process MCP sections if present
    if 'mcp' in toml_config:
        try:
            mcp_mapping = mcp_config_from_toml(toml_config['mcp'])
            if 'mcp' in mcp_mapping:
                cfg.mcp = mcp_mapping['mcp']
        except (TypeError, KeyError, ValidationError) as e:
            logger.openhands_logger.warning(
                f'Cannot parse MCP config from toml, values have not been applied.\nError: {e}'
            )
        except ValueError:
            raise ValueError('Error in MCP sections in config.toml')

    # Process kubernetes section if present
    if 'kubernetes' in toml_config:
        try:
            kubernetes_mapping = KubernetesConfig.from_toml_section(
                toml_config['kubernetes']
            )
            if 'kubernetes' in kubernetes_mapping:
                cfg.kubernetes = kubernetes_mapping['kubernetes']
        except (TypeError, KeyError, ValidationError) as e:
            logger.openhands_logger.warning(
                f'Cannot parse [kubernetes] config from toml, values have not been applied.\nError: {e}'
            )

    # Process condenser section if present
    if 'condenser' in toml_config:
        try:
            # Pass the LLM configs to the condenser config parser
            condenser_mapping = condenser_config_from_toml_section(
                toml_config['condenser'], cfg.llms
            )
            # Assign the default condenser configuration to the default agent configuration
            if 'condenser' in condenser_mapping:
                # Get the default agent config and assign the condenser config to it
                default_agent_config = cfg.get_agent_config()
                default_agent_config.condenser = condenser_mapping['condenser']
                logger.openhands_logger.debug(
                    'Default condenser configuration loaded from config toml and assigned to default agent'
                )
        except (TypeError, KeyError, ValidationError) as e:
            logger.openhands_logger.warning(
                f'Cannot parse [condenser] config from toml, values have not been applied.\nError: {e}'
            )
    # If no condenser section is in toml but enable_default_condenser is True,
    # set LLMSummarizingCondenserConfig as default
    elif cfg.enable_default_condenser:
        from openhands.core.config.condenser_config import LLMSummarizingCondenserConfig

        # Get default agent config
        default_agent_config = cfg.get_agent_config()

        # Create default LLM summarizing condenser config
        default_condenser = LLMSummarizingCondenserConfig(
            llm_config=cfg.get_llm_config(),  # Use default LLM config
            type='llm',
        )

        # Set as default condenser
        default_agent_config.condenser = default_condenser
        logger.openhands_logger.debug(
            'Default LLM summarizing condenser assigned to default agent (no condenser in config)'
        )

    # Process extended section if present
    if 'extended' in toml_config:
        try:
            cfg.extended = ExtendedConfig(toml_config['extended'])
        except (TypeError, KeyError, ValidationError) as e:
            logger.openhands_logger.warning(
                f'Cannot parse [extended] config from toml, values have not been applied.\nError: {e}'
            )

    # Check for unknown sections
    known_sections = {
        'core',
        'extended',
        'agent',
        'llm',
        'security',
        'sandbox',
        'condenser',
        'mcp',
        'kubernetes',
        'model_routing',
    }
    for key in toml_config:
        if key.lower() not in known_sections:
            logger.openhands_logger.warning(f'Unknown section [{key}] in {toml_file}')