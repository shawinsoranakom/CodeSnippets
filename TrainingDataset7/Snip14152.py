def restart_with_reloader():
    new_environ = {**os.environ, DJANGO_AUTORELOAD_ENV: "true"}
    orig = getattr(sys, "orig_argv", ())
    if any(
        (arg == "-u")
        or (
            arg.startswith("-")
            and not arg.startswith(("--", "-X", "-W"))
            and len(arg) > 2
            and arg[1:].isalpha()
            and "u" in arg
        )
        for arg in orig[1:]
    ):
        new_environ.setdefault("PYTHONUNBUFFERED", "1")
    args = get_child_arguments()
    while True:
        p = subprocess.run(args, env=new_environ, close_fds=False)
        if p.returncode != 3:
            return p.returncode