def run_support_container(
    args: EnvironmentConfig,
    context: str,
    image: str,
    name: str,
    ports: list[int],
    aliases: t.Optional[list[str]] = None,
    start: bool = True,
    cleanup: bool = True,
    cmd: t.Optional[list[str]] = None,
    env: t.Optional[dict[str, str]] = None,
    options: t.Optional[list[str]] = None,
    publish_ports: bool = True,
    data_container: bool = False,
) -> t.Optional[ContainerDescriptor]:
    """
    Start a container used to support tests, but not run them.
    Containers created this way will be accessible from tests.
    """
    name = get_session_container_name(args, name)

    if args.prime_containers:
        docker_pull(args, image)
        return None

    # SSH is required for publishing ports, as well as modifying the hosts file.
    # Initializing the SSH key here makes sure it is available for use after delegation.
    SshKey(args)

    aliases = aliases or [sanitize_host_name(name)]

    docker_command = require_docker().command
    current_container_id = get_docker_container_id()

    if docker_command == 'docker':
        if isinstance(args.controller, DockerConfig) and all(isinstance(target, (ControllerConfig, DockerConfig)) for target in args.targets):
            publish_ports = False  # publishing ports is not needed when test hosts are on the docker network

        if current_container_id:
            publish_ports = False  # publishing ports is pointless if already running in a docker container

    options = options or []

    if start:
        options.append('-dt')  # the -t option is required to cause systemd in the container to log output to the console

    if publish_ports:
        for port in ports:
            options.extend(['-p', str(port)])

    if env:
        for key, value in env.items():
            options.extend(['--env', '%s=%s' % (key, value)])

    max_open_files = detect_host_properties(args).max_open_files

    options.extend(['--ulimit', 'nofile=%s' % max_open_files])

    if args.dev_systemd_debug:
        options.extend(('--env', 'SYSTEMD_LOG_LEVEL=debug'))

    display.info('Starting new "%s" container.' % name)
    docker_pull(args, image)
    support_container_id = run_container(args, image, name, options, create_only=not start, cmd=cmd)
    running = start

    descriptor = ContainerDescriptor(
        image,
        context,
        name,
        support_container_id,
        ports,
        aliases,
        publish_ports,
        running,
        cleanup,
        env,
        data_container,
    )

    with support_containers_mutex:
        if name in support_containers:
            raise Exception(f'Container already defined: {name}')

        if not support_containers:
            ExitHandler.register(cleanup_containers, args)

        support_containers[name] = descriptor

    display.info(f'Adding "{name}" to container database.')

    if start:
        descriptor.register(args)

    return descriptor