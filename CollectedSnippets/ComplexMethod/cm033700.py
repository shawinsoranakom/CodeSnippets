def command_shell(args: ShellConfig) -> None:
    """Entry point for the `shell` command."""
    if not args.export and not args.cmd and not sys.stdin.isatty():
        raise ApplicationError('Standard input must be a TTY to launch a shell.')

    host_state = prepare_profiles(args, skip_setup=args.raw)  # shell

    if args.delegate:
        raise Delegate(host_state=host_state)

    install_requirements(args, host_state.controller_profile, host_state.controller_profile.python)  # shell

    if args.raw and not isinstance(args.controller, OriginConfig):
        display.warning('The --raw option will only be applied to the target.')

    target_profile = t.cast(SshTargetHostProfile, host_state.target_profiles[0])

    if isinstance(target_profile, ControllerProfile):
        # run the shell locally unless a target was requested
        con: Connection = LocalConnection(args)

        if args.export:
            display.info('Configuring controller inventory.', verbosity=1)
            create_controller_inventory(args, args.export, host_state.controller_profile)
    else:
        # a target was requested, connect to it over SSH
        con = target_profile.get_controller_target_connections()[0]

        if args.export:
            display.info('Configuring target inventory.', verbosity=1)
            create_posix_inventory(args, args.export, host_state.target_profiles, True)

    if args.export:
        return

    if isinstance(con, LocalConnection) and isinstance(target_profile, DebuggableProfile) and target_profile.debugging_enabled:
        # HACK: ensure the debugger port visible in the shell is the forwarded port, not the original
        args.metadata.debugger_settings = dataclasses.replace(args.metadata.debugger_settings, port=target_profile.debugger_port)

    with contextlib.nullcontext() if data_context().content.unsupported else metadata_context(args):
        if args.cmd:
            non_interactive_shell(args, target_profile, con)
        else:
            interactive_shell(args, target_profile, con)