def setup(cls, config: OpenHandsConfig, headless_mode: bool = False):
        should_check_dependencies = os.getenv('SKIP_DEPENDENCY_CHECK', '') != '1'
        if should_check_dependencies:
            code_repo_path = os.path.dirname(os.path.dirname(openhands.__file__))
            check_browser = config.enable_browser and sys.platform != 'win32'
            check_dependencies(code_repo_path, check_browser)

        initial_num_warm_servers = int(os.getenv('INITIAL_NUM_WARM_SERVERS', '0'))
        # Initialize warm servers if needed
        if initial_num_warm_servers > 0 and len(_WARM_SERVERS) == 0:
            plugins = _get_plugins(config)

            # Copy the logic from Runtime where we add a VSCodePlugin on init if missing
            if not headless_mode and not DISABLE_VSCODE_PLUGIN:
                plugins.append(VSCodeRequirement())

            for _ in range(initial_num_warm_servers):
                _create_warm_server(config, plugins)