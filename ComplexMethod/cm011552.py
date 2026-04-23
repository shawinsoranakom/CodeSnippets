def tail_logfile(
    header: str,
    file: str,
    dst: TextIO,
    finished: Event,
    interval_sec: float,
    log_line_filter: Callable[[str], bool] | None = None,
):
    while not os.path.exists(file):
        if finished.is_set():
            return
        time.sleep(interval_sec)

    with open(file, errors="replace") as fp:
        while True:
            line = fp.readline()

            if line:
                if log_line_filter and log_line_filter(line):
                    dst.write(f"{header}{line}")
            else:  # reached EOF
                if finished.is_set():
                    # log line producer is finished
                    break
                else:
                    # log line producer is still going
                    # wait for a bit before looping again
                    time.sleep(interval_sec)