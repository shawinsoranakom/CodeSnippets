def collect_requirements(
    python: PythonConfig,
    controller: bool,
    ansible: bool,
    coverage: bool,
    minimize: bool,
    command: t.Optional[str],
    sanity: t.Optional[str],
) -> list[PipCommand]:
    """Collect requirements for the given Python using the specified arguments."""
    commands: list[PipCommand] = []

    if coverage:
        commands.extend(collect_package_install(packages=[f'coverage=={get_coverage_version(python.version).coverage_version}'], constraints=False))

    if ansible or command:
        commands.extend(collect_general_install(command, ansible))

    if sanity:
        commands.extend(collect_sanity_install(sanity))

    if command == 'units':
        commands.extend(collect_units_install())

    if command in ('integration', 'windows-integration', 'network-integration'):
        commands.extend(collect_integration_install(command, controller))

    if (sanity or minimize) and any(isinstance(command, PipInstall) for command in commands):
        # bootstrap the managed virtual environment, which will have been created without any installed packages
        # sanity tests which install no packages skip this step
        commands = collect_bootstrap(python) + commands

        # most infrastructure packages can be removed from sanity test virtual environments after they've been created
        # removing them reduces the size of environments cached in containers
        uninstall_packages = list(get_venv_packages(python))

        commands.extend(collect_uninstall(packages=uninstall_packages))

    return commands