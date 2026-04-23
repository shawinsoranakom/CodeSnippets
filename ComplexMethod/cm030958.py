def strace_python(code, strace_flags, check=True):
    """Run strace and return the trace.

    Sets strace_returncode and python_returncode to `-1` on error."""
    res = None

    def _make_error(reason, details):
        return StraceResult(
            strace_returncode=-1,
            python_returncode=-1,
            event_bytes= f"error({reason},details={details!r}) = -1".encode('utf-8'),
            stdout=res.out if res else b"",
            stderr=res.err if res else b"")

    # Run strace, and get out the raw text
    try:
        res, cmd_line = run_python_until_end(
            "-c",
            textwrap.dedent(code),
            __run_using_command=[_strace_binary] + strace_flags,
        )
    except OSError as err:
        return _make_error("Caught OSError", err)

    if check and res.rc:
        res.fail(cmd_line)

    # Get out program returncode
    stripped = res.err.strip()
    output = stripped.rsplit(b"\n", 1)
    if len(output) != 2:
        return _make_error("Expected strace events and exit code line",
                           stripped[-50:])

    returncode_match = _returncode_regex.match(output[1])
    if not returncode_match:
        return _make_error("Expected to find returncode in last line.",
                           output[1][:50])

    python_returncode = int(returncode_match["returncode"])
    if check and python_returncode:
        res.fail(cmd_line)

    return StraceResult(strace_returncode=res.rc,
                        python_returncode=python_returncode,
                        event_bytes=output[0],
                        stdout=res.out,
                        stderr=res.err)