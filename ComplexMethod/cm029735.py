def main(args=None, *, _wrap_timer=None):
    """Main program, used when run as a script.

    The optional 'args' argument specifies the command line to be parsed,
    defaulting to sys.argv[1:].

    The return value is an exit code to be passed to sys.exit(); it
    may be None to indicate success.

    When an exception happens during timing, a traceback is printed to
    stderr and the return value is 1.  Exceptions at other times
    (including the template compilation) are not caught.

    '_wrap_timer' is an internal interface used for unit testing.  If it
    is not None, it must be a callable that accepts a timer function
    and returns another timer function (used for unit testing).
    """
    import getopt
    if args is None:
        args = sys.argv[1:]
    import _colorize
    colorize = _colorize.can_colorize()
    theme = _colorize.get_theme(force_color=colorize).timeit
    reset = theme.reset

    try:
        opts, args = getopt.getopt(args, "n:u:s:r:pt:vh",
                                   ["number=", "setup=", "repeat=",
                                    "process", "target-time=",
                                    "verbose", "unit=", "help"])
    except getopt.error as err:
        print(err)
        print("use -h/--help for command line help")
        return 2

    timer = default_timer
    stmt = "\n".join(args) or "pass"
    number = 0  # auto-determine
    target_time = default_target_time
    setup = []
    repeat = default_repeat
    verbose = 0
    time_unit = None
    units = {"nsec": 1e-9, "usec": 1e-6, "msec": 1e-3, "sec": 1.0}
    precision = 3
    for o, a in opts:
        if o in ("-n", "--number"):
            number = int(a)
        if o in ("-s", "--setup"):
            setup.append(a)
        if o in ("-u", "--unit"):
            if a in units:
                time_unit = a
            else:
                print("Unrecognized unit. Please select nsec, usec, msec, or sec.",
                      file=sys.stderr)
                return 2
        if o in ("-r", "--repeat"):
            repeat = int(a)
            if repeat <= 0:
                repeat = 1
        if o in ("-p", "--process"):
            timer = time.process_time
        if o in ("-t", "--target-time"):
            target_time = float(a)
        if o in ("-v", "--verbose"):
            if verbose:
                precision += 1
            verbose += 1
        if o in ("-h", "--help"):
            print(__doc__, end="")
            return 0
    setup = "\n".join(setup) or "pass"

    # Include the current directory, so that local imports work (sys.path
    # contains the directory of this script, rather than the current
    # directory)
    import os
    sys.path.insert(0, os.curdir)
    if _wrap_timer is not None:
        timer = _wrap_timer(timer)

    t = Timer(stmt, setup, timer)
    if number == 0:
        # determine number so that total time >= target_time
        callback = None
        if verbose:
            def callback(number, time_taken):
                s = "" if number == 1 else "s"
                print(
                    f"{number} loop{s} "
                    f"{theme.punctuation}-> "
                    f"{theme.timing}{time_taken:.{precision}g} sec{reset}"
                )

        try:
            number, _ = t.autorange(callback, target_time)
        except:
            t.print_exc(colorize=colorize)
            return 1

        if verbose:
            print()

    try:
        raw_timings = t.repeat(repeat, number)
    except:
        t.print_exc(colorize=colorize)
        return 1

    def format_time(dt):
        unit = time_unit

        if unit is not None:
            scale = units[unit]
        else:
            scales = [(scale, unit) for unit, scale in units.items()]
            scales.sort(reverse=True)
            for scale, unit in scales:
                if dt >= scale:
                    break

        return "%.*g %s" % (precision, dt / scale, unit)

    if verbose:
        raw = f"{theme.punctuation}, ".join(
            f"{theme.timing}{t}" for t in map(format_time, raw_timings)
        )
        print(f"raw times: {raw}{reset}")
        print()
    timings = [dt / number for dt in raw_timings]

    best = min(timings)
    worst = max(timings)
    s = "" if number == 1 else "s"
    print(
        f"{number} loop{s}, best of {repeat}: "
        f"{theme.best}{format_time(best)}{reset} "
        f"{theme.per_loop}per loop{reset}"
    )

    if worst >= best * 4:
        import warnings

        print(file=sys.stderr)
        warnings.warn_explicit(
            f"{theme.warning}The test results are likely unreliable. "
            f"The {theme.warning_worst}worst time ({format_time(worst)})"
            f"{theme.warning} was more than four times slower than the "
            f"{theme.warning_best}best time ({format_time(best)})"
            f"{theme.warning}.{reset}",
            UserWarning, "", 0,
        )
    return None