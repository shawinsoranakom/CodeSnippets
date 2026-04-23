def start_edge(listen_str: str, use_ssl: bool = True, asynchronous: bool = False):
    if listen_str:
        listen = parse_gateway_listen(
            listen_str, default_host=config.default_ip, default_port=constants.DEFAULT_PORT_EDGE
        )
    else:
        listen = config.GATEWAY_LISTEN

    if len(listen) == 0:
        raise ValueError("no listen addresses provided")

    # separate privileged and unprivileged addresses
    unprivileged, privileged = split_list_by(listen, lambda addr: addr.is_unprivileged() or False)

    # if we are root, we can directly bind to privileged ports as well
    if is_root():
        unprivileged = unprivileged + privileged
        privileged = []

    # check that we are actually started the gateway server
    if not unprivileged:
        unprivileged = parse_gateway_listen(
            f":{get_free_tcp_port()}",
            default_host=config.default_ip,
            default_port=constants.DEFAULT_PORT_EDGE,
        )

    # bind the gateway server to unprivileged addresses
    edge_thread = do_start_edge(unprivileged, use_ssl=use_ssl, asynchronous=True)

    # start TCP proxies for the remaining addresses
    proxy_destination = unprivileged[0]
    for address in privileged:
        # escalate to root
        args = [
            "proxy",
            "--gateway-listen",
            str(address),
            "--target-address",
            str(proxy_destination),
        ]
        run_module_as_sudo(
            module="localstack.services.edge",
            arguments=args,
            asynchronous=True,
        )

    if edge_thread is not None:
        edge_thread.join()