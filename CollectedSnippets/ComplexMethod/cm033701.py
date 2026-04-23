def interactive_shell(
    args: ShellConfig,
    target_profile: SshTargetHostProfile,
    con: Connection,
) -> None:
    """Run an interactive shell."""
    if isinstance(con, SshConnection) and args.raw:
        cmd: list[str] = []
    elif isinstance(target_profile, PosixProfile):
        cmd = []

        if args.raw:
            shell = 'sh'  # shell required for non-ssh connection
        else:
            shell = 'bash'

            python = target_profile.python  # make sure the python interpreter has been initialized before opening a shell
            display.info(f'Target Python {python.version} is at: {python.path}')

            env = get_environment_variables(args, target_profile, con)
            cmd = get_env_command(env)

        cmd += [shell, '-i']
    else:
        cmd = []

    try:
        con.run(cmd, capture=False, interactive=True)
    except SubprocessError as ex:
        if isinstance(con, SshConnection) and ex.status == 255:
            # 255 indicates SSH itself failed, rather than a command run on the remote host.
            # In this case, report a host connection error so additional troubleshooting output is provided.
            if not args.delegate and not args.host_path:

                def callback() -> None:
                    """Callback to run during error display."""
                    target_profile.on_target_failure()  # when the controller is not delegated, report failures immediately

            else:
                callback = None

            raise HostConnectionError(f'SSH shell connection failed for host {target_profile.config}: {ex}', callback) from ex

        raise