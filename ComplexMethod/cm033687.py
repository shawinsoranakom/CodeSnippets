def integration_environment(
    args: IntegrationConfig,
    target: IntegrationTarget,
    test_dir: str,
    inventory_path: str,
    ansible_config: t.Optional[str],
    env_config: t.Optional[CloudEnvironmentConfig],
    test_env: IntegrationEnvironment,
    host_state: HostState,
) -> dict[str, str]:
    """Return a dictionary of environment variables to use when running the given integration test target."""
    env = ansible_environment(args, ansible_config=ansible_config)

    callback_plugins = ['junit'] + (env_config.callback_plugins or [] if env_config else [])

    integration = dict(
        JUNIT_OUTPUT_DIR=ResultType.JUNIT.path,
        JUNIT_TASK_RELATIVE_PATH=test_env.test_dir,
        JUNIT_REPLACE_OUT_OF_TREE_PATH='out-of-tree:',
        ANSIBLE_CALLBACKS_ENABLED=','.join(sorted(set(callback_plugins))),
        ANSIBLE_TEST_CI=args.metadata.ci_provider or get_ci_provider().code,
        ANSIBLE_TEST_COVERAGE='check' if args.coverage_check else ('yes' if args.coverage else ''),
        ANSIBLE_TEST_ANSIBLE_VERSION=get_ansible_version(),
        OUTPUT_DIR=test_dir,
        INVENTORY_PATH=os.path.abspath(inventory_path),
    )

    if args.debug_strategy:
        env.update(ANSIBLE_STRATEGY='debug')

    if isinstance(host_state.controller_profile, DebuggableProfile):
        env.update(host_state.controller_profile.get_ansible_cli_environment_variables())

    if 'non_local/' in target.aliases:
        if args.coverage:
            display.warning('Skipping coverage reporting on Ansible modules for non-local test: %s' % target.name)

        env.update(ANSIBLE_TEST_REMOTE_INTERPRETER='')

    env.update(integration)
    env.update(target.env_set)

    return env