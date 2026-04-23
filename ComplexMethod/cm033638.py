def get_docker_preferred_network_name(args: EnvironmentConfig) -> t.Optional[str]:
    """
    Return the preferred network name for use with Docker. The selection logic is:
    - the network selected by the user with `--docker-network`
    - the network of the currently running docker container (if any)
    - the default docker network (returns None)
    """
    try:
        return get_docker_preferred_network_name.network  # type: ignore[attr-defined]
    except AttributeError:
        pass

    network = None

    if args.docker_network:
        network = args.docker_network
    else:
        current_container_id = get_docker_container_id()

        if current_container_id:
            try:
                # Make sure any additional containers we launch use the same network as the current container we're running in.
                # This is needed when ansible-test is running in a container that is not connected to Docker's default network.
                container = docker_inspect(args, current_container_id, always=True)
                network = container.get_network_name()
            except ContainerNotFoundError:
                display.warning('Unable to detect the network for the current container. Use the `--docker-network` option if containers are unreachable.')

    # The default docker behavior puts containers on the same network.
    # The default podman behavior puts containers on isolated networks which don't allow communication between containers or network disconnect.
    # Starting with podman version 2.1.0 rootless containers are able to join networks.
    # Starting with podman version 2.2.0 containers can be disconnected from networks.
    # To maintain feature parity with docker, detect and use the default "podman" network when running under podman.
    if network is None and require_docker().command == 'podman' and docker_network_inspect(args, 'podman', always=True):
        network = 'podman'

    get_docker_preferred_network_name.network = network  # type: ignore[attr-defined]

    return network