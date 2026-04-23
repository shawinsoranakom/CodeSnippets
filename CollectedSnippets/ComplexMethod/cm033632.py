def collect_integration_install(command: str, controller: bool) -> list[PipInstall]:
    """Return details necessary for the specified integration pip install(s)."""
    requirements_paths: list[tuple[str, str]] = []
    constraints_paths: list[tuple[str, str]] = []

    # Support for prefixed files was added to ansible-test in ansible-core 2.12 when split controller/target testing was implemented.
    # Previous versions of ansible-test only recognize non-prefixed files.
    # If a prefixed file exists (even if empty), it takes precedence over the non-prefixed file.
    prefixes = ('controller.' if controller else 'target.', '')

    for prefix in prefixes:
        path = os.path.join(data_context().content.integration_path, f'{prefix}requirements.txt')

        if os.path.exists(path):
            requirements_paths.append((data_context().content.root, path))
            break

    for prefix in prefixes:
        path = os.path.join(data_context().content.integration_path, f'{command}.{prefix}requirements.txt')

        if os.path.exists(path):
            requirements_paths.append((data_context().content.root, path))
            break

    for prefix in prefixes:
        path = os.path.join(data_context().content.integration_path, f'{prefix}constraints.txt')

        if os.path.exists(path):
            constraints_paths.append((data_context().content.root, path))
            break

    return collect_install(requirements_paths, constraints_paths)