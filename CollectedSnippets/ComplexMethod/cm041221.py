def start_dns_server(port: int, asynchronous: bool = False, standalone: bool = False):
    if DNS_SERVER:
        # already started - bail
        LOG.error("DNS servers are already started. Avoid starting again.")
        return

    # check if DNS server is disabled
    if not config.use_custom_dns():
        LOG.debug("Not starting DNS. DNS_ADDRESS=%s", config.DNS_ADDRESS)
        return

    upstream_dns = get_fallback_dns_server()
    if not upstream_dns:
        LOG.warning("Error starting the DNS server: No upstream dns server found.")
        return

    # host to bind the DNS server to. In docker we always want to bind to "0.0.0.0"
    host = config.DNS_ADDRESS
    if in_docker():
        host = "0.0.0.0"

    if port_can_be_bound(Port(port, "udp"), address=host):
        start_server(port=port, host=host, upstream_dns=upstream_dns)
        if not asynchronous:
            sleep_forever()
        return

    if standalone:
        LOG.debug("Already in standalone mode and port binding still fails.")
        return

    start_dns_server_as_sudo(port)