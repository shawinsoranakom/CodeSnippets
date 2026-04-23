def register_cluster(
    host: str, path: str, forward_url: str, custom_endpoint: CustomEndpoint
) -> list[Rule]:
    """
    Registers routes for a cluster at the edge router.
    Depending on which endpoint strategy is employed, and if a custom endpoint is enabled, different routes are
    registered.
    This method is tightly coupled with `cluster_manager.build_cluster_endpoint`, which already creates the
    endpoint URL according to the configuration used here.

    :param host: hostname of the inbound address without scheme or port
    :param path: path of the inbound address
    :param forward_url: whole address for outgoing traffic (including the protocol)
    :param custom_endpoint: Object that stores a custom address and if its enabled.
            If a custom_endpoint is set AND enabled, the specified address takes precedence
            over any strategy currently active, and overwrites any host/path combination.
    :return: a list of generated router rules, which can be used for removal
    """
    # custom backends overwrite the usual forward_url
    forward_url = config.OPENSEARCH_CUSTOM_BACKEND or forward_url

    # if the opensearch security plugin is enabled, only TLS connections are allowed, but the cert cannot be verified
    client = SimpleRequestsClient()
    client.session.verify = False
    endpoint = ProxyHandler(forward_url, client)

    rules = []
    strategy = config.OPENSEARCH_ENDPOINT_STRATEGY
    # custom endpoints override any endpoint strategy
    if custom_endpoint and custom_endpoint.enabled:
        LOG.debug("Registering route from %s%s to %s", host, path, endpoint.proxy.forward_base_url)
        assert not (host == localstack_host().host and (not path or path == "/")), (
            "trying to register an illegal catch all route"
        )
        rules.append(
            ROUTER.add(
                path=path,
                endpoint=endpoint,
                host=f"{host}<port:port>",
            )
        )
        rules.append(
            ROUTER.add(
                f"{path}/<path:path>",
                endpoint=endpoint,
                host=f"{host}<port:port>",
            )
        )
    elif strategy == "domain":
        LOG.debug("Registering route from %s to %s", host, endpoint.proxy.forward_base_url)
        assert not host == localstack_host().host, "trying to register an illegal catch all route"
        rules.append(
            ROUTER.add(
                "/",
                endpoint=endpoint,
                host=f"{host}<port:port>",
            )
        )
        rules.append(
            ROUTER.add(
                "/<path:path>",
                endpoint=endpoint,
                host=f"{host}<port:port>",
            )
        )
    elif strategy == "path":
        LOG.debug("Registering route from %s to %s", path, endpoint.proxy.forward_base_url)
        assert path and not path == "/", "trying to register an illegal catch all route"
        rules.append(ROUTER.add(path, endpoint=endpoint))
        rules.append(ROUTER.add(f"{path}/<path:path>", endpoint=endpoint))

    elif strategy != "port":
        LOG.warning("Attempted to register route for cluster with invalid strategy '%s'", strategy)

    return rules