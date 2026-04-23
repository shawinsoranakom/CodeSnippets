def delegate_command(args: EnvironmentConfig, host_state: HostState, exclude: list[str], require: list[str]) -> None:
    """Delegate execution based on the provided host state."""
    con = host_state.controller_profile.get_origin_controller_connection()
    working_directory = host_state.controller_profile.get_working_directory()
    host_delegation = not isinstance(args.controller, OriginConfig)

    if host_delegation:
        if data_context().content.collection:
            content_root = os.path.join(working_directory, data_context().content.collection.directory)
        else:
            content_root = os.path.join(working_directory, 'ansible')

        ansible_bin_path = os.path.join(working_directory, 'ansible', 'bin')

        with tempfile.NamedTemporaryFile(prefix='ansible-source-', suffix='.tgz') as payload_file:
            create_payload(args, payload_file.name)
            con.extract_archive(chdir=working_directory, src=payload_file)
    else:
        content_root = working_directory
        ansible_bin_path = get_ansible_bin_path(args)

    command = generate_command(args, host_state.controller_profile.python, ansible_bin_path, content_root, exclude, require)

    if isinstance(con, SshConnection):
        ssh = con.settings
    else:
        ssh = None

    options = []

    if isinstance(args, IntegrationConfig) and args.controller.is_managed and all(target.is_managed for target in args.targets):
        if not args.allow_destructive:
            options.append('--allow-destructive')

    with support_container_context(args, ssh) as containers:  # type: t.Optional[ContainerDatabase]
        if containers:
            options.extend(['--containers', json.dumps(containers.to_dict())])

        # Run unit tests unprivileged to prevent stray writes to the source tree.
        # Also disconnect from the network once requirements have been installed.
        if isinstance(args, UnitsConfig) and isinstance(con, DockerConnection):
            pytest_user = 'pytest'

            writable_dirs = [
                os.path.join(content_root, ResultType.JUNIT.relative_path),
                os.path.join(content_root, ResultType.COVERAGE.relative_path),
            ]

            con.run(['mkdir', '-p'] + writable_dirs, capture=True)
            con.run(['chmod', '777'] + writable_dirs, capture=True)
            con.run(['chmod', '755', working_directory], capture=True)
            con.run(['useradd', pytest_user, '--create-home'], capture=True)

            con.run(insert_options(command, options + ['--requirements-mode', 'only']), capture=False)

            container = con.inspect()
            networks = container.get_network_names()

            if networks is not None:
                if args.metadata.debugger_flags.enable:
                    networks = []
                    display.warning('Skipping network isolation to enable remote debugging.')

                for network in networks:
                    try:
                        con.disconnect_network(network)
                    except SubprocessError:
                        display.warning(
                            'Unable to disconnect network "%s" (this is normal under podman). '
                            'Tests will not be isolated from the network. Network-related tests may '
                            'misbehave.' % (network,)
                        )
            else:
                display.warning('Network disconnection is not supported (this is normal under podman). '
                                'Tests will not be isolated from the network. Network-related tests may misbehave.')

            options.extend(['--requirements-mode', 'skip'])

            con.user = pytest_user

        success = False
        status = 0

        try:
            # When delegating, preserve the original separate stdout/stderr streams, but only when the following conditions are met:
            # 1) Display output is being sent to stderr. This indicates the output on stdout must be kept separate from stderr.
            # 2) The delegation is non-interactive. Interactive mode, which generally uses a TTY, is not compatible with intercepting stdout/stderr.
            # The downside to having separate streams is that individual lines of output from each are more likely to appear out-of-order.
            output_stream = OutputStream.ORIGINAL if args.display_stderr and not args.interactive else None
            con.run(insert_options(command, options), capture=False, interactive=args.interactive, output_stream=output_stream)
            success = True
        except SubprocessError as ex:
            status = ex.status
            raise
        finally:
            if host_delegation:
                download_results(args, con, content_root, success)

            if not success and status == STATUS_HOST_CONNECTION_ERROR:
                for target in host_state.target_profiles:
                    target.on_target_failure()