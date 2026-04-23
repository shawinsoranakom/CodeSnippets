def prepare_profiles[TEnvironmentConfig: EnvironmentConfig](
    args: TEnvironmentConfig,
    targets_use_pypi: bool = False,
    skip_setup: bool = False,
    requirements: t.Optional[c.Callable[[HostProfile], None]] = None,
) -> HostState:
    """
    Create new profiles, or load existing ones, and return them.
    If a requirements callback was provided, it will be used before configuring hosts if delegation has already been performed.
    """
    if args.host_path:
        host_state = HostState.deserialize(args, os.path.join(args.host_path, 'state.dat'))
    else:
        run_pypi_proxy(args, targets_use_pypi)

        controller_host_profile = t.cast(ControllerHostProfile, create_host_profile(args, args.controller, None))

        host_state = HostState(
            controller_profile=controller_host_profile,
            target_profiles=[create_host_profile(args, target, controller_host_profile) for target in args.targets],
        )

        if args.prime_containers:
            for host_profile in host_state.profiles:
                if isinstance(host_profile, DockerProfile):
                    host_profile.provision()

            raise PrimeContainers()

        ExitHandler.register(functools.partial(cleanup_profiles, host_state))

        for pre_profile in host_state.profiles:
            pre_profile.pre_provision()

        def provision(profile: HostProfile) -> None:
            """Provision the given profile."""
            profile.provision()

            if not skip_setup:
                profile.setup()

        dispatch_jobs(
            [(profile, WrappedThread(functools.partial(provision, profile), f'Provision: {profile}')) for profile in host_state.profiles]
        )

        host_state.controller_profile.configure()

    if not args.delegate:
        check_controller_python(args, host_state)
        check_controller_powershell(args, host_state)

        if requirements:
            requirements(host_state.controller_profile)

        def configure(profile: HostProfile) -> None:
            """Configure the given profile."""
            profile.wait()

            if not skip_setup:
                profile.configure()

            if requirements:
                requirements(profile)

        dispatch_jobs(
            [(profile, WrappedThread(functools.partial(configure, profile), f'Configure: {profile}')) for profile in host_state.target_profiles]
        )

    return host_state