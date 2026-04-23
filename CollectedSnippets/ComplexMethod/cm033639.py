def create_container_database(args: EnvironmentConfig) -> ContainerDatabase:
    """Create and return a container database with information necessary for all test hosts to make use of relevant support containers."""
    origin: dict[str, dict[str, ContainerAccess]] = {}
    control: dict[str, dict[str, ContainerAccess]] = {}
    managed: dict[str, dict[str, ContainerAccess]] = {}

    for name, container in support_containers.items():
        if container.data_container:
            # data containers will not be started, and will be missing details
            continue
        if container.details.published_ports:
            if require_docker().command == 'podman':
                host_ip_func = get_podman_host_ip
            else:
                host_ip_func = get_docker_host_ip
            published_access = ContainerAccess(
                host_ip=host_ip_func(),
                names=container.aliases,
                ports=None,
                forwards=dict((port, published_port) for port, published_port in container.details.published_ports.items()),
            )
        else:
            published_access = None  # no published access without published ports (ports are only published if needed)

        if container.details.container_ip:
            # docker containers, and rootfull podman containers should have a container IP address
            container_access = ContainerAccess(
                host_ip=container.details.container_ip,
                names=container.aliases,
                ports=container.ports,
                forwards=None,
            )
        elif require_docker().command == 'podman':
            # published ports for rootless podman containers should be accessible from the host's IP
            container_access = ContainerAccess(
                host_ip=get_podman_host_ip(),
                names=container.aliases,
                ports=None,
                forwards=dict((port, published_port) for port, published_port in container.details.published_ports.items()),
            )
        else:
            container_access = None  # no container access without an IP address

        if get_docker_container_id():
            if not container_access:
                raise Exception('Missing IP address for container: %s' % name)

            origin_context = origin.setdefault(container.context, {})
            origin_context[name] = container_access
        elif not published_access:
            pass  # origin does not have network access to the containers
        else:
            origin_context = origin.setdefault(container.context, {})
            origin_context[name] = published_access

        if isinstance(args.controller, RemoteConfig):
            pass  # SSH forwarding required
        elif '-controller-' in name:
            pass  # hack to avoid exposing the controller container to the controller
        elif isinstance(args.controller, DockerConfig) or (isinstance(args.controller, OriginConfig) and get_docker_container_id()):
            if container_access:
                control_context = control.setdefault(container.context, {})
                control_context[name] = container_access
            else:
                raise Exception('Missing IP address for container: %s' % name)
        else:
            if not published_access:
                raise Exception('Missing published ports for container: %s' % name)

            control_context = control.setdefault(container.context, {})
            control_context[name] = published_access

        if issubclass(args.target_type, (RemoteConfig, WindowsInventoryConfig, PosixSshConfig)):
            pass  # SSH forwarding required
        elif '-controller-' in name or '-target-' in name:
            pass  # hack to avoid exposing the controller and target containers to the target
        elif issubclass(args.target_type, DockerConfig) or (issubclass(args.target_type, OriginConfig) and get_docker_container_id()):
            if container_access:
                managed_context = managed.setdefault(container.context, {})
                managed_context[name] = container_access
            else:
                raise Exception('Missing IP address for container: %s' % name)
        else:
            if not published_access:
                raise Exception('Missing published ports for container: %s' % name)

            managed_context = managed.setdefault(container.context, {})
            managed_context[name] = published_access

    data = {
        HostType.origin: origin,
        HostType.control: control,
        HostType.managed: managed,
    }

    data = dict((key, value) for key, value in data.items() if value)

    return ContainerDatabase(data)