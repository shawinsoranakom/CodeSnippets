def setup_config_from_args(args: argparse.Namespace) -> OpenHandsConfig:
    """Load config from toml and override with command line arguments.

    Common setup used by both CLI and main.py entry points.

    Configuration precedence (from highest to lowest):
    1. CLI parameters (e.g., -l for LLM config)
    2. config.toml in current directory (or --config-file location if specified)
    3. ~/.openhands/settings.json and ~/.openhands/config.toml
    """
    # Load base config from toml and env vars
    config = load_openhands_config(config_file=args.config_file)

    # Override with command line arguments if provided
    if args.llm_config:
        logger.openhands_logger.debug(f'CLI specified LLM config: {args.llm_config}')

        # Check if the LLM config is NOT in the loaded configs
        if args.llm_config not in config.llms:
            # Try to load from the specified config file
            llm_config = get_llm_config_arg(args.llm_config, args.config_file)

            # If not found in the specified config file, try the user's config.toml
            if llm_config is None and args.config_file != os.path.join(
                os.path.expanduser('~'), '.openhands', 'config.toml'
            ):
                user_config = os.path.join(
                    os.path.expanduser('~'), '.openhands', 'config.toml'
                )
                if os.path.exists(user_config):
                    logger.openhands_logger.debug(
                        f"Trying to load LLM config '{args.llm_config}' from user config: {user_config}"
                    )
                    llm_config = get_llm_config_arg(args.llm_config, user_config)
        else:
            # If it's already in the loaded configs, use that
            llm_config = config.llms[args.llm_config]
            logger.openhands_logger.debug(
                f"Using LLM config '{args.llm_config}' from loaded configuration"
            )
        if llm_config is None:
            raise ValueError(
                f"Cannot find LLM configuration '{args.llm_config}' in any config file"
            )

        # Set this as the default LLM config (highest precedence)
        config.set_llm_config(llm_config)
        logger.openhands_logger.debug(
            f'Set LLM config from CLI parameter: {args.llm_config}'
        )

    # Override default agent if provided
    if hasattr(args, 'agent_cls') and args.agent_cls:
        config.default_agent = args.agent_cls

    # Set max iterations and max budget per task if provided, otherwise fall back to config values
    if hasattr(args, 'max_iterations') and args.max_iterations is not None:
        config.max_iterations = args.max_iterations
    if hasattr(args, 'max_budget_per_task') and args.max_budget_per_task is not None:
        config.max_budget_per_task = args.max_budget_per_task

    # Read selected repository in config for use by CLI and main.py
    if hasattr(args, 'selected_repo') and args.selected_repo is not None:
        config.sandbox.selected_repo = args.selected_repo

    return config