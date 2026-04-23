def run_command(path: str, options: list[str], origin: Origin) -> tuple[str, str, str]:
    """Run an inventory script, normalize and validate output."""
    cmd = [path] + options

    try:
        sp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as ex:
        raise AnsibleError(
            message=f"Failed to execute inventory script command {shlex.join(cmd)!r}.",
            # obj will be added by inventory manager
        ) from ex

    stdout_bytes, stderr_bytes = sp.communicate()

    stderr = stderr_bytes.decode(errors='surrogateescape')

    if stderr and not stderr.endswith('\n'):
        stderr += '\n'

    # DTFIX-FUTURE: another use case for the "not quite help text, definitely not message" diagnostic output on errors
    stderr_help_text = f'Standard error from inventory script:\n{stderr}' if stderr.strip() else None

    if sp.returncode != 0:
        raise AnsibleError(
            message=f"Inventory script returned non-zero exit code {sp.returncode}.",
            help_text=stderr_help_text,
            # obj will be added by inventory manager
        )

    try:
        data = stdout_bytes.decode()
    except Exception as ex:
        raise AnsibleError(
            "Inventory script result contained characters that cannot be interpreted as UTF-8.",
            help_text=stderr_help_text,
            # obj will be added by inventory manager
        ) from ex
    else:
        data = TrustedAsTemplate().tag(origin.tag(data))

    return data, stderr, stderr_help_text