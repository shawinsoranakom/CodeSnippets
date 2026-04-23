def run_command(
    cmd: str,
    use_shell: bool = False,
    log_cmd: bool = True,
    cwd: str | None = None,
    env: dict | None = None,
    check: bool = True,
) -> int:
    """Run a command with optional shell execution."""
    if use_shell:
        args = cmd
        log_prefix = "[shell]"
        executable = "/bin/bash"
    else:
        args = shlex.split(cmd)
        log_prefix = "[cmd]"
        executable = None

    if log_cmd:
        display_cmd = cmd if use_shell else " ".join(args)
        logger.info("%s %s", log_prefix, display_cmd)

    run_env = {**os.environ, **(env or {})}

    proc = subprocess.run(
        args,
        shell=use_shell,
        executable=executable,
        stdout=sys.stdout,
        stderr=sys.stderr,
        cwd=cwd,
        env=run_env,
        check=False,
    )

    if check and proc.returncode != 0:
        logger.error(
            "%s Command failed (exit %s): %s", log_prefix, proc.returncode, cmd
        )
        raise subprocess.CalledProcessError(
            proc.returncode, args if not use_shell else cmd
        )

    return proc.returncode