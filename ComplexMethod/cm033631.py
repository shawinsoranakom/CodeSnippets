def run_pip(
    args: EnvironmentConfig,
    python: PythonConfig,
    commands: list[PipCommand],
    connection: t.Optional[Connection],
) -> None:
    """Run the specified pip commands for the given Python, and optionally the specified host."""
    connection = connection or LocalConnection(args)
    script = prepare_pip_script(commands)

    if isinstance(args, IntegrationConfig):
        # Integration tests can involve two hosts (controller and target).
        # The connection type can be used to disambiguate between the two.
        context = " (controller)" if isinstance(connection, LocalConnection) else " (target)"
    else:
        context = ""

    if isinstance(python, VirtualPythonConfig):
        context += " [venv]"

    # The interpreter path is not included below.
    # It can be seen by running ansible-test with increased verbosity (showing all commands executed).
    display.info(f'Installing requirements for Python {python.version}{context}')

    if not args.explain:
        try:
            connection.run([python.path], data=script, capture=False)
        except SubprocessError:
            script = prepare_pip_script([PipVersion()])

            try:
                connection.run([python.path], data=script, capture=True)
            except SubprocessError as ex:
                if 'pip is unavailable:' in ex.stdout + ex.stderr:
                    raise PipUnavailableError(python) from None

            raise