def load_debugger_settings(args: EnvironmentConfig) -> None:
    """Load the remote debugger settings."""
    use_debugger: type[DebuggerSettings] | None = None

    if args.metadata.debugger_flags.on_demand:
        # On-demand debugging only enables debugging if we're running under a debugger, otherwise it's a no-op.

        for candidate_debugger in get_subclasses(DebuggerSettings):
            if candidate_debugger.is_active():
                use_debugger = candidate_debugger
                break
        else:
            display.info('Debugging disabled because no debugger was detected.', verbosity=1)
            args.metadata.debugger_flags = DebuggerFlags.all(False)
            return

        display.info('Enabling on-demand debugging.', verbosity=1)

        if not args.metadata.debugger_flags.enable:
            # Assume the user wants all debugging features enabled, since on-demand debugging with no features is pointless.
            args.metadata.debugger_flags = DebuggerFlags.all(True)

    if not args.metadata.debugger_flags.enable:
        return

    if not use_debugger:  # detect debug type based on env var
        for candidate_debugger in get_subclasses(DebuggerSettings):
            if candidate_debugger.get_config_env_var_name() in os.environ:
                use_debugger = candidate_debugger
                break
        else:
            display.info('Debugging disabled because no debugger configuration was provided.', verbosity=1)
            args.metadata.debugger_flags = DebuggerFlags.all(False)
            return

    config = os.environ.get(use_debugger.get_config_env_var_name()) or '{}'
    settings = use_debugger.parse(config)
    args.metadata.debugger_settings = settings

    display.info(f'>>> Debugger Settings ({use_debugger.get_debug_type()})\n{json.dumps(dataclasses.asdict(settings), indent=4)}', verbosity=3)