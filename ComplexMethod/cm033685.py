def command_integration_script(
    args: IntegrationConfig,
    host_state: HostState,
    target: IntegrationTarget,
    test_dir: str,
    inventory_path: str,
    coverage_manager: CoverageManager,
):
    """Run an integration test script."""
    display.info('Running %s integration test script' % target.name)

    if not os.access(target.script_path, os.X_OK):
        raise ApplicationError(f'Unable to run non-executable script {target.script_path!r}. Did you forget to run "chmod +x" on it?')

    env_config = None

    if isinstance(args, PosixIntegrationConfig):
        cloud_environment = get_cloud_environment(args, target)

        if cloud_environment:
            env_config = cloud_environment.get_environment_config()

    if env_config:
        display.info('>>> Environment Config\n%s' % json.dumps(dict(
            env_vars=env_config.env_vars,
            ansible_vars=env_config.ansible_vars,
            callback_plugins=env_config.callback_plugins,
            module_defaults=env_config.module_defaults,
        ), indent=4, sort_keys=True), verbosity=3)

    with integration_test_environment(args, target, inventory_path) as test_env:  # type: IntegrationEnvironment
        cmd = ['./%s' % os.path.basename(target.script_path)]

        if args.verbosity:
            cmd.append('-' + ('v' * args.verbosity))

        env = integration_environment(args, target, test_dir, test_env.inventory_path, test_env.ansible_config, env_config, test_env, host_state)
        cwd = os.path.join(test_env.targets_dir, target.relative_path)

        env.update(
            # support use of adhoc ansible commands in collections without specifying the fully qualified collection name
            ANSIBLE_PLAYBOOK_DIR=cwd,
        )

        if env_config and env_config.env_vars:
            env.update(env_config.env_vars)

        with integration_test_config_file(args, env_config, test_env.integration_dir) as config_path:  # type: t.Optional[str]
            if config_path:
                cmd += ['-e', '@%s' % config_path]

            test_env.update_environment(env)
            env.update(coverage_manager.get_environment(target.name, target.aliases))
            env.update(get_powershell_injector_env(host_state.controller_profile.powershell, env))
            cover_python(args, host_state.controller_profile.python, cmd, target.name, env, cwd=cwd, capture=False)