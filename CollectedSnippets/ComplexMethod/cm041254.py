def get_endpoint_for_network(network: str | None = None) -> str:
    """
    Get the LocalStack endpoint (= IP address) on the given network.
    If a network is given, it will return the IP address/hostname of LocalStack on that network
    If omitted, it will return the IP address/hostname of the main container network
    This is a cached call, clear cache if networks might have changed

    :param network: Network to return the endpoint for
    :return: IP address or hostname of LS on the given network
    """
    container_name = get_main_container_name()
    network = network or get_main_container_network()
    main_container_ip = None
    try:
        if config.is_in_docker:
            main_container_ip = DOCKER_CLIENT.get_container_ipv4_for_network(
                container_name_or_id=container_name,
                container_network=network,
            )
        else:
            # default gateway for the network should be the host
            # In a Linux host-mode environment, the default gateway for the network should be the IP of the host
            if config.is_in_linux:
                main_container_ip = DOCKER_CLIENT.inspect_network(network)["IPAM"]["Config"][0][
                    "Gateway"
                ]
            else:
                # In a non-Linux host-mode environment, we need to determine the IP of the host by running a container
                # (basically macOS host mode, i.e. this is a feature to improve the developer experience)
                image_name = constants.DOCKER_IMAGE_NAME
                out, _ = DOCKER_CLIENT.run_container(
                    image_name,
                    remove=True,
                    entrypoint="",
                    command=["ping", "-c", "1", "host.docker.internal"],
                )
                out = out.decode(config.DEFAULT_ENCODING) if isinstance(out, bytes) else out
                ip = re.match(r"PING[^\(]+\(([^\)]+)\).*", out, re.MULTILINE | re.DOTALL)
                ip = ip and ip.group(1)
                if ip:
                    main_container_ip = ip
        LOG.info("Determined main container target IP: %s", main_container_ip)
    except Exception as e:
        LOG.info("Unable to get main container IP address: %s", e)

    if not main_container_ip:
        # fall back to returning the hostname/IP of the Docker host, if we cannot determine the main container IP
        return get_docker_host_from_container()

    return main_container_ip