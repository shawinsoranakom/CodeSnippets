def test_open(testfn):
    # SSLContext.load_dh_params uses Py_fopen() rather than normal open()
    try:
        import ssl

        load_dh_params = ssl.create_default_context().load_dh_params
    except ImportError:
        load_dh_params = None

    try:
        import readline
    except ImportError:
        readline = None

    def rl(name):
        if readline:
            return getattr(readline, name, None)
        else:
            return None

    # Try a range of "open" functions.
    # All of them should fail
    with TestHook(raise_on_events={"open"}) as hook:
        for fn, *args in [
            (open, testfn, "r"),
            (open, sys.executable, "rb"),
            (open, 3, "wb"),
            (open, testfn, "w", -1, None, None, None, False, lambda *a: 1),
            (load_dh_params, testfn),
            (rl("read_history_file"), testfn),
            (rl("read_history_file"), None),
            (rl("write_history_file"), testfn),
            (rl("write_history_file"), None),
            (rl("append_history_file"), 0, testfn),
            (rl("append_history_file"), 0, None),
            (rl("read_init_file"), testfn),
            (rl("read_init_file"), None),
        ]:
            if not fn:
                continue
            with assertRaises(RuntimeError):
                try:
                    fn(*args)
                except NotImplementedError:
                    if fn == load_dh_params:
                        # Not callable in some builds
                        load_dh_params = None
                        raise RuntimeError
                    else:
                        raise

    actual_mode = [(a[0], a[1]) for e, a in hook.seen if e == "open" and a[1]]
    actual_flag = [(a[0], a[2]) for e, a in hook.seen if e == "open" and not a[1]]
    assertSequenceEqual(
        [
            i
            for i in [
                (testfn, "r"),
                (sys.executable, "r"),
                (3, "w"),
                (testfn, "w"),
                (testfn, "rb") if load_dh_params else None,
                (testfn, "r") if readline else None,
                ("~/.history", "r") if readline else None,
                (testfn, "w") if readline else None,
                ("~/.history", "w") if readline else None,
                (testfn, "a") if rl("append_history_file") else None,
                ("~/.history", "a") if rl("append_history_file") else None,
                (testfn, "r") if readline else None,
                ("<readline_init_file>", "r") if readline else None,
            ]
            if i is not None
        ],
        actual_mode,
    )
    assertSequenceEqual([], actual_flag)