def generic_service_test_matching_rule(
    changed_file_path: str,
    api_dependencies: dict[str, Iterable[str]] | None = None,
    search_patterns: Iterable[str] = DEFAULT_SEARCH_PATTERNS,
    test_dirs: Iterable[str] = ("tests/aws/services",),
) -> set[str]:
    """
    Generic matching of changes in service files to their tests

    :param api_dependencies: dict of API dependencies where each key is the service and its value a list of services it depends on
    :param changed_file_path: the file path of the detected change
    :param search_patterns: list of regex patterns to search for in the changed file path
    :param test_dirs: list of test directories to match for a changed service
    :return: list of partial test file path filters for the matching service and all services it depends on
    """
    # TODO: consider API_COMPOSITES

    if api_dependencies is None:
        from localstack.utils.bootstrap import API_DEPENDENCIES, API_DEPENDENCIES_OPTIONAL

        # merge the mandatory and optional service dependencies
        api_dependencies = defaultdict(set)
        for service, mandatory_dependencies in API_DEPENDENCIES.items():
            api_dependencies[service].update(mandatory_dependencies)

        for service, optional_dependencies in API_DEPENDENCIES_OPTIONAL.items():
            api_dependencies[service].update(optional_dependencies)

    match = None
    for pattern in search_patterns:
        match = re.findall(pattern, changed_file_path)
        if match:
            break

    if match:
        changed_service = match[0]
        changed_services = [changed_service]
        service_dependencies = resolve_dependencies(changed_service, api_dependencies)
        changed_services.extend(service_dependencies)
        changed_service_module_names = [_map_to_module_name(svc) for svc in changed_services]
        return {
            f"{test_dir}/{svc}/" for test_dir in test_dirs for svc in changed_service_module_names
        }

    return set()