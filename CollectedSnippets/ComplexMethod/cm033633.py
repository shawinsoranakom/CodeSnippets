def collect_install(
    requirements_paths: list[tuple[str, str]],
    constraints_paths: list[tuple[str, str]],
    packages: t.Optional[list[str]] = None,
    constraints: bool = True,
) -> list[PipInstall]:
    """Build a pip install list from the given requirements, constraints and packages."""
    # listing content constraints first gives them priority over constraints provided by ansible-test
    constraints_paths = list(constraints_paths)

    if constraints:
        constraints_paths.append((ANSIBLE_TEST_DATA_ROOT, os.path.join(ANSIBLE_TEST_DATA_ROOT, 'requirements', 'constraints.txt')))

    requirements = [(os.path.relpath(path, root), read_text_file(path)) for root, path in requirements_paths if usable_pip_file(path)]
    constraints = [(os.path.relpath(path, root), read_text_file(path)) for root, path in constraints_paths if usable_pip_file(path)]
    packages = packages or []

    if requirements or packages:
        installs = [PipInstall(
            requirements=requirements,
            constraints=constraints,
            packages=packages,
        )]
    else:
        installs = []

    return installs