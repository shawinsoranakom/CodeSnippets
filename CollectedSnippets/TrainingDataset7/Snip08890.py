def popen_wrapper(args, stdout_encoding="utf-8"):
    """
    Friendly wrapper around Popen.

    Return stdout output, stderr output, and OS status code.
    """
    try:
        p = run(args, capture_output=True, close_fds=os.name != "nt")
    except OSError as err:
        raise CommandError("Error executing %s" % args[0]) from err
    return (
        p.stdout.decode(stdout_encoding),
        p.stderr.decode(DEFAULT_LOCALE_ENCODING, errors="replace"),
        p.returncode,
    )