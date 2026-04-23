def finalize_config(cfg: OpenHandsConfig) -> None:
    """More tweaks to the config after it's been loaded."""
    # Handle the sandbox.volumes parameter
    if cfg.sandbox.volumes is not None:
        # Split by commas to handle multiple mounts
        mounts = cfg.sandbox.volumes.split(',')

        # Check if any mount explicitly targets /workspace
        workspace_mount_found = False
        for mount in mounts:
            parts = mount.split(':')
            if len(parts) >= 2 and parts[1] == '/workspace':
                workspace_mount_found = True
                host_path = os.path.abspath(parts[0])

                # Set the workspace_mount_path and workspace_mount_path_in_sandbox
                cfg.workspace_mount_path = host_path
                cfg.workspace_mount_path_in_sandbox = '/workspace'

                # Also set workspace_base
                cfg.workspace_base = host_path
                break

        # If no explicit /workspace mount was found, don't set any workspace mount
        # This allows users to mount volumes without affecting the workspace
        if not workspace_mount_found:
            logger.openhands_logger.debug(
                'No explicit /workspace mount found in SANDBOX_VOLUMES. '
                'Using default workspace path in sandbox.'
            )
            # Ensure workspace_mount_path and workspace_base are None to avoid
            # unintended mounting behavior
            cfg.workspace_mount_path = None
            cfg.workspace_base = None

        # Validate all mounts
        for mount in mounts:
            parts = mount.split(':')
            if len(parts) < 2 or len(parts) > 3:
                raise ValueError(
                    f'Invalid mount format in sandbox.volumes: {mount}. '
                    f"Expected format: 'host_path:container_path[:mode]', e.g. '/my/host/dir:/workspace:rw'"
                )

    # Handle the deprecated workspace_* parameters
    elif cfg.workspace_base is not None or cfg.workspace_mount_path is not None:
        if cfg.workspace_base is not None:
            cfg.workspace_base = os.path.abspath(cfg.workspace_base)
            if cfg.workspace_mount_path is None:
                cfg.workspace_mount_path = cfg.workspace_base

        if cfg.workspace_mount_rewrite:
            base = cfg.workspace_base or os.getcwd()
            parts = cfg.workspace_mount_rewrite.split(':')
            cfg.workspace_mount_path = base.replace(parts[0], parts[1])

    # make sure log_completions_folder is an absolute path
    for llm in cfg.llms.values():
        llm.log_completions_folder = os.path.abspath(llm.log_completions_folder)

    if cfg.sandbox.use_host_network and platform.system() == 'Darwin':
        logger.openhands_logger.warning(
            'Please upgrade to Docker Desktop 4.29.0 or later to use host network mode on macOS. '
            'See https://github.com/docker/roadmap/issues/238#issuecomment-2044688144 for more information.'
        )

    # make sure cache dir exists
    if cfg.cache_dir:
        pathlib.Path(cfg.cache_dir).mkdir(parents=True, exist_ok=True)

    if not cfg.jwt_secret:
        cfg.jwt_secret = SecretStr(
            get_or_create_jwt_secret(
                get_file_store(cfg.file_store, cfg.file_store_path)
            )
        )

    # If CLIRuntime is selected, disable Jupyter for all agents
    # Assuming 'cli' is the identifier for CLIRuntime
    if cfg.runtime and cfg.runtime.lower() == 'cli':
        for age_nt_name, agent_config in cfg.agents.items():
            if agent_config.enable_jupyter:
                agent_config.enable_jupyter = False
            if agent_config.enable_browsing:
                agent_config.enable_browsing = False
        logger.openhands_logger.debug(
            'Automatically disabled Jupyter plugin and browsing for all agents '
            'because CLIRuntime is selected and does not support IPython execution.'
        )