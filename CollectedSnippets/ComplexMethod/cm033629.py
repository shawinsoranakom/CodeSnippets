def install_requirements(
    args: EnvironmentConfig,
    host_profile: HostProfile | None,
    python: PythonConfig,
    ansible: bool = False,
    command: bool = False,
    coverage: bool = False,
    controller: bool = True,
    connection: t.Optional[Connection] = None,
) -> None:
    """Install requirements for the given Python using the specified arguments."""
    create_result_directories(args)

    if not requirements_allowed(args, controller):
        post_install(host_profile)
        return

    if command and isinstance(args, (UnitsConfig, IntegrationConfig)) and args.coverage:
        coverage = True

    if ansible:
        try:
            ansible_cache = install_requirements.ansible_cache  # type: ignore[attr-defined]
        except AttributeError:
            ansible_cache = install_requirements.ansible_cache = {}  # type: ignore[attr-defined]

        ansible_installed = ansible_cache.get(python.path)

        if ansible_installed:
            ansible = False
        else:
            ansible_cache[python.path] = True

    commands = collect_requirements(
        python=python,
        controller=controller,
        ansible=ansible,
        command=args.command if command else None,
        coverage=coverage,
        minimize=False,
        sanity=None,
    )

    from .host_profiles import DebuggableProfile

    if isinstance(host_profile, DebuggableProfile) and host_profile.debugger and host_profile.debugger.get_python_package():
        commands.append(PipInstall(
            requirements=[],
            constraints=[],
            packages=[host_profile.debugger.get_python_package()],
        ))

    if not commands:
        post_install(host_profile)
        return

    run_pip(args, python, commands, connection)

    # false positive: pylint: disable=no-member
    if any(isinstance(command, PipInstall) and command.has_package('pyyaml') for command in commands):
        check_pyyaml(python)

    post_install(host_profile)