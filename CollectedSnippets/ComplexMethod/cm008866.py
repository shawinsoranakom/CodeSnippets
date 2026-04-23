def get_min_version_from_toml(
    toml_path: str,
    versions_for: str,
    python_version: str,
    *,
    include: list | None = None,
):
    # Parse the TOML file
    with open(toml_path, "rb") as file:
        toml_data = tomllib.load(file)

    dependencies = defaultdict(list)
    for dep in toml_data["project"]["dependencies"]:
        requirement = Requirement(dep)
        dependencies[requirement.name].append(requirement)

    # Initialize a dictionary to store the minimum versions
    min_versions = {}

    # Iterate over the libs in MIN_VERSION_LIBS
    for lib in set(MIN_VERSION_LIBS + (include or [])):
        if versions_for == "pull_request" and lib in SKIP_IF_PULL_REQUEST:
            # some libs only get checked on release because of simultaneous
            # changes in multiple libs
            continue
        # Check if the lib is present in the dependencies
        if lib in dependencies:
            if include and lib not in include:
                continue
            requirements = dependencies[lib]
            for requirement in requirements:
                if _check_python_version_from_requirement(requirement, python_version):
                    version_string = str(requirement.specifier)
                    break

            # Use parse_version to get the minimum supported version from version_string
            min_version = get_minimum_version(lib, version_string)

            # Store the minimum version in the min_versions dictionary
            min_versions[lib] = min_version

    return min_versions