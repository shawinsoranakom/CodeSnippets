def ansible_environment(args: CommonConfig, color: bool = True, ansible_config: t.Optional[str] = None) -> dict[str, str]:
    """Return a dictionary of environment variables to use when running Ansible commands."""
    env = common_environment()
    path = env['PATH']

    ansible_bin_path = get_ansible_bin_path(args)

    if not path.startswith(ansible_bin_path + os.path.pathsep):
        path = ansible_bin_path + os.path.pathsep + path

    if not ansible_config:
        # use the default empty configuration unless one has been provided
        ansible_config = args.get_ansible_config()

    if not args.explain and not os.path.exists(ansible_config):
        raise ApplicationError('Configuration not found: %s' % ansible_config)

    ansible = dict(
        ANSIBLE_PYTHON_MODULE_RLIMIT_NOFILE=str(SOFT_RLIMIT_NOFILE),
        ANSIBLE_INVENTORY_PLUGIN_EXTS='.yaml, .yml, .json, .winrm, .networking',  # allows the yaml/json inventory format for windows and networking
        ANSIBLE_FORCE_COLOR='%s' % 'true' if args.color and color else 'false',
        ANSIBLE_FORCE_HANDLERS='true',  # allow cleanup handlers to run when tests fail
        ANSIBLE_HOST_PATTERN_MISMATCH='error',  # prevent tests from unintentionally passing when hosts are not found
        ANSIBLE_INVENTORY='/dev/null',  # force tests to provide inventory
        ANSIBLE_DEPRECATION_WARNINGS='false',
        ANSIBLE_HOST_KEY_CHECKING='false',
        ANSIBLE_RETRY_FILES_ENABLED='false',
        ANSIBLE_DISPLAY_TRACEBACK=args.display_traceback,
        ANSIBLE_CONFIG=ansible_config,
        ANSIBLE_LIBRARY='/dev/null',
        ANSIBLE_DEVEL_WARNING='false',  # Don't show warnings that CI is running devel
        PYTHONPATH=get_ansible_python_path(args),
        PAGER='/bin/cat',
        PATH=path,
        # give TQM worker processes time to report code coverage results
        # without this the last task in a play may write no coverage file, an empty file, or an incomplete file
        # enabled even when not using code coverage to surface warnings when worker processes do not exit cleanly
        ANSIBLE_WORKER_SHUTDOWN_POLL_COUNT='100',
        ANSIBLE_WORKER_SHUTDOWN_POLL_DELAY='0.1',
        # ansible-test specific environment variables require an 'ANSIBLE_TEST_' prefix to distinguish them from ansible-core env vars defined by config
        ANSIBLE_TEST_ANSIBLE_LIB_ROOT=ANSIBLE_LIB_ROOT,  # used by the coverage injector
    )

    if isinstance(args, IntegrationConfig) and args.coverage:
        # standard path injection is not effective for the persistent connection helper, instead the location must be configured
        # it only requires the injector for code coverage
        # the correct python interpreter is already selected using the sys.executable used to invoke ansible
        ansible.update(
            _ANSIBLE_CONNECTION_PATH=os.path.join(get_python_injector_path(), 'ansible_connection_cli_stub.py'),
        )

    if isinstance(args, PosixIntegrationConfig):
        ansible.update(
            ANSIBLE_PYTHON_INTERPRETER='/set/ansible_python_interpreter/in/inventory',  # force tests to set ansible_python_interpreter in inventory
        )

    env.update(ansible)

    if args.debug:
        env.update(
            ANSIBLE_DEBUG='true',
            ANSIBLE_LOG_PATH=os.path.join(ResultType.LOGS.name, 'debug.log'),
        )

    if data_context().content.collection:
        env.update(
            ANSIBLE_COLLECTIONS_PATH=data_context().content.collection.root,
        )

    if data_context().content.is_ansible:
        env.update(configure_plugin_paths(args))

    return env