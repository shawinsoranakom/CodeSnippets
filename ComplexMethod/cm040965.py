def build_cluster_endpoint(
    domain_key: DomainKey,
    custom_endpoint: CustomEndpoint | None = None,
    engine_type: EngineType = EngineType.OpenSearch,
    preferred_port: int | None = None,
) -> str:
    """
    Builds the cluster endpoint from and optional custom_endpoint and the localstack opensearch config. Example
    values:

    - my-domain.us-east-1.opensearch.localhost.localstack.cloud:4566 (endpoint strategy = domain (default))
    - localhost:4566/us-east-1/my-domain (endpoint strategy = path)
    - localhost:[port-from-range] (endpoint strategy = port (or deprecated 'off'))
    - my.domain:443/foo (arbitrary endpoints (technically not allowed by AWS, but there are no rules in localstack))

    If preferred_port is not None, it is tried to reserve the given port. If the port is already bound, another port
    will be used.
    """
    # If we have a CustomEndpoint, we directly take its endpoint.
    if custom_endpoint and custom_endpoint.enabled:
        return custom_endpoint.endpoint

    # different endpoints based on engine type
    engine_domain = "opensearch" if engine_type == EngineType.OpenSearch else "es"

    # Otherwise, the endpoint is either routed through the edge proxy via a sub-path (localhost:4566/opensearch/...)
    if config.OPENSEARCH_ENDPOINT_STRATEGY == "port":
        if preferred_port is not None:
            try:
                # if the preferred port is given, we explicitly try to reserve it
                assigned_port = external_service_ports.reserve_port(preferred_port)
            except PortNotAvailableException:
                LOG.warning(
                    "Preferred port %s is not available, trying to reserve another port.",
                    preferred_port,
                )
                assigned_port = external_service_ports.reserve_port()
        else:
            assigned_port = external_service_ports.reserve_port()

        host_definition = localstack_host(custom_port=assigned_port)
        return host_definition.host_and_port()
    if config.OPENSEARCH_ENDPOINT_STRATEGY == "path":
        host_definition = localstack_host()
        return f"{host_definition.host_and_port()}/{engine_domain}/{domain_key.region}/{domain_key.domain_name}"

    # or through a subdomain (domain-name.region.opensearch.localhost.localstack.cloud)
    host_definition = localstack_host()
    return f"{domain_key.domain_name}.{domain_key.region}.{engine_domain}.{host_definition.host_and_port()}"