def generate_buffer_output(
    input_stream: list,
    duration,
    hop,
    delay,
    cutoff,
):
    now = 0
    buffer = {}
    output = []
    for entry in input_stream:
        last_time = now
        now = max(now, entry["time"])

        to_process: list = []
        windows = get_windows(duration, hop, entry["time"])
        for _pw_window_start, _pw_window_end in windows:
            shard = None
            window = (shard, _pw_window_start, _pw_window_end)
            freeze_threshold = window[2] + cutoff
            if freeze_threshold <= now:
                continue

            threshold = window[1] + delay

            if threshold <= now:
                to_process.append((window, entry))
            else:
                key = (window, entry["value"])
                buffer[key] = entry

        bufkeys = list(buffer.keys())

        for window, value in bufkeys:
            entry = buffer[(window, value)]
            threshold = window[1] + delay
            if last_time != now and threshold <= now and threshold > last_time:
                to_process.append((window, entry))
                buffer.pop((window, value))

        output.extend(to_process)

    # flush buffer
    bufkeys = list(buffer.keys())
    for window, value in bufkeys:
        entry = buffer.pop((window, value))
        output.append((window, entry))

    return output