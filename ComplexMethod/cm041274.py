def container_ports_can_be_bound(
    ports: IntOrPort | list[IntOrPort],
    address: str | None = None,
) -> bool:
    """Determine whether a given list of ports can be bound by Docker containers

    :param ports: single port or list of ports to check
    :return: True iff all ports can be bound
    """
    port_mappings = PortMappings(bind_host=address or "")
    for port in ensure_list(ports):
        port = Port.wrap(port)
        port_mappings.add(port.port, port.port, protocol=port.protocol)
    try:
        result = DOCKER_CLIENT.run_container(
            _get_ports_check_docker_image(),
            entrypoint="sh",
            command=["-c", "echo test123"],
            ports=port_mappings,
            remove=True,
        )
    except DockerNotAvailable as e:
        LOG.warning("Cannot perform port check because Docker is not available.")
        raise e
    except Exception as e:
        if "port is already allocated" not in str(e) and "address already in use" not in str(e):
            LOG.warning(
                "Unexpected error when attempting to determine container port status",
                exc_info=LOG.isEnabledFor(logging.DEBUG),
            )
        return False
    # TODO(srw): sometimes the command output from the docker container is "None", particularly when this function is
    #  invoked multiple times consecutively. Work out why.
    if to_str(result[0] or "").strip() != "test123":
        LOG.warning(
            "Unexpected output when attempting to determine container port status: %s", result
        )
    return True