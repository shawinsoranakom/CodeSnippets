def determine_aws_service_model(
    request: Request, services: ServiceCatalog = None
) -> ServiceModel | None:
    """
    Tries to determine the name of the AWS service an incoming request is targeting.
    :param request: to determine the target service name of
    :param services: service catalog (can be handed in for caching purposes)
    :return: service name string (or None if the targeting service could not be determined exactly)
    """
    services = services or get_service_catalog()
    signing_name, target_prefix, operation, host, path = _extract_service_indicators(request)
    candidates = set()

    # 1. check the signing names
    if signing_name:
        signing_name_candidates = services.by_signing_name(signing_name)
        if len(signing_name_candidates) == 1:
            # a unique signing-name -> service name mapping is the case for ~75% of service operations
            candidate = signing_name_candidates[0]
            return services.get(candidate.name, candidate.protocol)

        # try to find a match with the custom signing name rules
        custom_match = custom_signing_name_rules(signing_name, path)
        if custom_match:
            return services.get(custom_match.name, custom_match.protocol)

        # still ambiguous - add the services to the list of candidates
        candidates.update(signing_name_candidates)

    # 2. check the target prefix
    if target_prefix and operation:
        target_candidates = services.by_target_prefix(target_prefix)
        if len(target_candidates) == 1:
            # a unique target prefix
            candidate = target_candidates[0]
            return services.get(candidate.name, candidate.protocol)

        # still ambiguous - add the services to the list of candidates
        candidates.update(target_candidates)

        # exclude services where the operation is not contained in the service spec
        for service_identifier in list(candidates):
            service = services.get(service_identifier.name, service_identifier.protocol)
            if operation not in service.operation_names:
                candidates.remove(service_identifier)
    else:
        # exclude services which have a target prefix (the current request does not have one)
        for service_identifier in list(candidates):
            service = services.get(service_identifier.name, service_identifier.protocol)
            if service.metadata.get("targetPrefix") is not None:
                candidates.remove(service_identifier)

    if len(candidates) == 1:
        service_identifier = candidates.pop()
        return services.get(service_identifier.name, service_identifier.protocol)

    # 3. check the path if it is set and not a trivial root path
    if path and path != "/":
        # try to find a match with the custom path rules
        custom_path_match = custom_path_addressing_rules(path)
        if custom_path_match:
            return services.get(custom_path_match.name, custom_path_match.protocol)

    # 4. check the host (custom host addressing rules)
    if host:
        # iterate over the service spec's endpoint prefix
        for prefix, services_per_prefix in services.endpoint_prefix_index.items():
            # this prevents a virtual host addressed bucket to be wrongly recognized
            if host.startswith(f"{prefix}.") and ".s3." not in host:
                if len(services_per_prefix) == 1:
                    candidate = services_per_prefix[0]
                    return services.get(candidate.name, candidate.protocol)
                candidates.update(services_per_prefix)

        custom_host_match = custom_host_addressing_rules(host)
        if custom_host_match:
            candidate = custom_host_match[0]
            return services.get(candidate.name, candidate.protocol)

    if request.shallow:
        # from here on we would need access to the request body, which doesn't exist for shallow requests like
        # WebsocketRequests.
        return None

    # 5. check the query / form-data
    try:
        values = request.values
        if "Action" in values:
            # query / ec2 protocol requests always have an action and a version (the action is more significant)
            query_candidates = [
                service
                for service in services.by_operation(values["Action"])
                if any(
                    is_protocol_in_service_model_identifier(protocol, service)
                    for protocol in ("ec2", "query")
                )
            ]

            if len(query_candidates) == 1:
                candidate = query_candidates[0]
                return services.get(candidate.name, candidate.protocol)

            if "Version" in values:
                for service_identifier in list(query_candidates):
                    service_model = services.get(
                        service_identifier.name, service_identifier.protocol
                    )
                    if values["Version"] != service_model.api_version:
                        # the combination of Version and Action is not unique, add matches to the candidates
                        query_candidates.remove(service_identifier)

            if len(query_candidates) == 1:
                candidate = query_candidates[0]
                return services.get(candidate.name, candidate.protocol)

            candidates.update(query_candidates)

    except RequestEntityTooLarge:
        # Some requests can be form-urlencoded but also contain binary data, which will fail the form parsing (S3 can
        # do this). In that case, skip this step and continue to try to determine the service name. The exception is
        # RequestEntityTooLarge even if the error is due to failed decoding.
        LOG.debug(
            "Failed to determine AWS service from request body because the form could not be parsed",
            exc_info=LOG.isEnabledFor(logging.DEBUG),
        )

    # 6. resolve service spec conflicts
    resolved_conflict = resolve_conflicts(candidates, request)
    if resolved_conflict:
        return services.get(resolved_conflict.name, resolved_conflict.protocol)

    # 7. check the legacy S3 rules in the end
    legacy_match = legacy_s3_rules(request)
    if legacy_match:
        return services.get(legacy_match.name, legacy_match.protocol)

    if signing_name:
        return services.get(name=signing_name)
    if candidates:
        candidate = candidates.pop()
        return services.get(candidate.name, candidate.protocol)
    return None