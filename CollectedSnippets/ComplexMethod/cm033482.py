def run(
    *args: t.Any,
    env: dict[str, t.Any] | None,
    cwd: pathlib.Path | str,
    capture_output: bool = False,
) -> CompletedProcess | None:
    """Run the specified command."""
    args = [arg.relative_to(cwd) if isinstance(arg, pathlib.Path) else arg for arg in args]

    str_args = tuple(path_to_str(arg) for arg in args)
    str_env = {key: path_to_str(value) for key, value in env.items()} if env is not None else None

    display.show(f"--> {shlex.join(str_args)}", color=Display.CYAN)

    try:
        p = subprocess.run(str_args, check=True, text=True, env=str_env, cwd=cwd, capture_output=capture_output)
    except subprocess.CalledProcessError as ex:
        # improve type hinting and include stdout/stderr (if any) in the message
        raise CalledProcessError(
            message=str(ex),
            cmd=str_args,
            status=ex.returncode,
            stdout=ex.stdout,
            stderr=ex.stderr,
        ) from None

    if not capture_output:
        return None

    # improve type hinting
    return CompletedProcess(
        stdout=p.stdout,
        stderr=p.stderr,
    )