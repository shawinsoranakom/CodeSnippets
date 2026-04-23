def _build_table(
    events,
    sort_by=None,
    header=None,
    row_limit=100,
    max_src_column_width=75,
    max_name_column_width=55,
    max_shapes_column_width=80,
    with_flops=False,
    profile_memory=False,
    top_level_events_only=False,
    time_unit=None,
):
    """Print a summary of events (which can be a list of FunctionEvent or FunctionEventAvg)."""
    if len(events) == 0:
        return ""

    has_device_time = any(event.self_device_time_total > 0 for event in events)
    has_device_mem = any(event.self_device_memory_usage > 0 for event in events)
    use_device = events[0].use_device
    # Running on PrivateUse1 device with profiler but not enable
    # ProfilerActivity.PrivateUse1 can also catch privateuse1 memory usage.
    # Here only need to check has_privateuse1_time if not use_device.
    if not use_device and has_device_time:
        raise RuntimeError("use_device is None, but there is device performance data.")

    has_input_shapes = any(
        (event.input_shapes is not None and len(event.input_shapes) > 0)
        for event in events
    )

    has_overload_names = any(
        (event.overload_name is not None and len(event.overload_name) > 0)
        for event in events
    )

    if sort_by is not None:
        events = EventList(
            sorted(
                events,
                key=lambda evt: getattr(
                    evt,
                    sort_by.replace("cuda", "device")
                    .replace("xpu", "device")
                    .replace("privateuse1", "device"),
                ),
                reverse=True,
            ),
            use_device=use_device,
            profile_memory=profile_memory,
            with_flops=with_flops,
        )

    name_column_width = max(len(evt.key) for evt in events) + 4
    if max_name_column_width is not None:
        name_column_width = min(name_column_width, max_name_column_width)

    shapes_column_width = max(len(str(evt.input_shapes)) for evt in events) + 4
    if max_shapes_column_width is not None:
        shapes_column_width = min(shapes_column_width, max_shapes_column_width)

    DEFAULT_COLUMN_WIDTH = 12
    flops_column_width = DEFAULT_COLUMN_WIDTH

    src_column_width = None
    stacks = [
        evt.stack for evt in events if evt.stack is not None and len(evt.stack) > 0
    ]
    has_stack = len(stacks) > 0
    if has_stack:
        src_column_width = (
            max(max(len(entry) for entry in stack) for stack in stacks) + 4
        )
        if max_src_column_width is not None:
            src_column_width = min(src_column_width, max_src_column_width)

    headers = ["Name"]
    if has_overload_names:
        headers.append("Overload Name")
    headers += [
        "Self CPU %",
        "Self CPU",
        "CPU total %",
        "CPU total",
        "CPU time avg",
    ]

    device_name = use_device.upper() if use_device is not None else "None"
    if has_device_time:
        headers.extend(
            [
                f"Self {device_name}",
                f"Self {device_name} %",
                f"{device_name} total",
                f"{device_name} time avg",
            ]
        )
    if profile_memory:
        headers.extend(
            [
                "CPU Mem",
                "Self CPU Mem",
            ]
        )
        if use_device and has_device_mem:
            headers.extend(
                [
                    f"{device_name} Mem",
                    f"Self {device_name} Mem",
                ]
            )
    headers.append("# of Calls")
    # Only append Node ID if any event has a valid (>= 0) Node ID
    append_node_id = any(evt.node_id != -1 for evt in events)
    if append_node_id:
        headers.append("Node ID")

    SPACING_SIZE = 2
    row_format_lst = [""]
    header_sep_lst = [""]
    line_length_lst = [-SPACING_SIZE]

    def add_column(padding, text_dir=">"):
        row_format_lst[0] += (
            "{: " + text_dir + str(padding) + "}" + (" " * SPACING_SIZE)
        )
        header_sep_lst[0] += "-" * padding + (" " * SPACING_SIZE)
        line_length_lst[0] += padding + SPACING_SIZE

    def auto_scale_flops(flops):
        flop_headers = [
            "FLOPs",
            "KFLOPs",
            "MFLOPs",
            "GFLOPs",
            "TFLOPs",
            "PFLOPs",
        ]
        if flops <= 0:
            raise AssertionError(f"Expected flops to be positive, but got {flops}")
        # pyrefly: ignore [no-matching-overload]
        log_flops = max(0, min(math.log10(flops) / 3, float(len(flop_headers) - 1)))
        if not (log_flops >= 0 and log_flops < len(flop_headers)):
            raise AssertionError(
                f"Expected log_flops to be in range [0, {len(flop_headers)}), but got {log_flops}"
            )
        return (pow(10, (math.floor(log_flops) * -3.0)), flop_headers[int(log_flops)])

    add_column(name_column_width)
    if has_overload_names:
        add_column(name_column_width)
    for _ in headers[1 + has_overload_names :]:
        add_column(DEFAULT_COLUMN_WIDTH)

    if has_input_shapes:
        headers.append("Input Shapes")
        add_column(shapes_column_width)

    if has_stack:
        headers.append("Source Location")
        add_column(src_column_width, text_dir="<")

    if with_flops:
        # Auto-scaling of flops header
        raw_flops = [evt.flops for evt in events if evt.flops > 0]
        if len(raw_flops) != 0:
            (flops_scale, flops_header) = auto_scale_flops(min(raw_flops))
            headers.append(f"Total {flops_header}")
            add_column(flops_column_width)
        else:
            with_flops = False  # can't find any valid flops

    row_format = row_format_lst[0]
    header_sep = header_sep_lst[0]
    line_length = line_length_lst[0]
    add_column = None  # type: ignore[assignment]

    result = []

    def append(s):
        result.append(s)
        result.append("\n")  # Yes, newline after the end as well

    sum_self_cpu_time_total = 0
    sum_self_device_time_total = 0
    for evt in events:
        sum_self_cpu_time_total += evt.self_cpu_time_total
        if evt.device_type == DeviceType.CPU and evt.is_legacy:
            # in legacy profiler, kernel info is stored in cpu events
            sum_self_device_time_total += evt.self_device_time_total
        elif (
            evt.device_type
            in [
                DeviceType.CUDA,
                DeviceType.PrivateUse1,
                DeviceType.MTIA,
                DeviceType.XPU,
            ]
            and not evt.is_user_annotation
        ):
            # in kineto profiler, there're events with the correct device type (e.g. CUDA)
            sum_self_device_time_total += evt.self_device_time_total

    # Actual printing
    if header is not None:
        append("=" * line_length)
        append(header)
    if top_level_events_only:
        append("=" * line_length)
        append("This report only display top-level ops statistics")
    append(header_sep)
    append(row_format.format(*headers))

    append(header_sep)

    def trim_path(path, src_column_width):
        if len(path) > src_column_width:
            offset = len(path) - src_column_width
            path = path[offset:]
            if len(path) > 3:
                path = "..." + path[3:]
        return path

    def override_time_unit(time_us, default_str, time_unit):
        US_IN_SECOND = 1000.0 * 1000.0
        US_IN_MS = 1000.0
        if time_unit == "s":
            return f"{time_us / US_IN_SECOND:.3f}s"
        elif time_unit == "ms":
            return f"{time_us / US_IN_MS:.3f}ms"
        elif time_unit == "us":
            return f"{time_us:.3f}us"
        else:
            return default_str

    event_limit = 0
    for evt in events:
        if event_limit == row_limit:
            break
        if top_level_events_only and evt.cpu_parent is not None:
            continue
        else:
            event_limit += 1
        name = evt.key
        if max_name_column_width is not None and len(name) >= max_name_column_width - 3:
            name = name[: (max_name_column_width - 3)] + "..."

        evt.self_cpu_percent = _format_time_share(
            evt.self_cpu_time_total, sum_self_cpu_time_total
        )
        evt.total_cpu_percent = (
            _format_time_share(evt.cpu_time_total, sum_self_cpu_time_total)
            if not evt.is_async
            else 0
        )

        row_values = [name]
        if has_overload_names:
            overload_name = evt.overload_name
            if (
                max_name_column_width is not None
                and len(overload_name) >= max_name_column_width - 3
            ):
                overload_name = overload_name[: (max_name_column_width - 3)] + "..."
            row_values += [overload_name]
        row_values += [
            # Self CPU total %, 0 for async events.
            evt.self_cpu_percent,
            override_time_unit(
                evt.self_cpu_time_total, evt.self_cpu_time_total_str, time_unit
            ),  # Self CPU total
            # CPU total %, 0 for async events.
            evt.total_cpu_percent,
            override_time_unit(
                evt.cpu_time_total, evt.cpu_time_total_str, time_unit
            ),  # CPU total
            override_time_unit(
                evt.cpu_time, evt.cpu_time_str, time_unit
            ),  # CPU time avg
        ]
        if has_device_time:
            evt.total_device_percent = _format_time_share(
                evt.self_device_time_total, sum_self_device_time_total
            )
            row_values.extend(
                [
                    override_time_unit(
                        evt.self_device_time_total,
                        evt.self_device_time_total_str,
                        time_unit,
                    ),
                    # device time total %
                    evt.total_device_percent,
                    override_time_unit(
                        evt.device_time_total, evt.device_time_total_str, time_unit
                    ),
                    override_time_unit(
                        evt.device_time, evt.device_time_str, time_unit
                    ),  # device time avg
                ]
            )
        if profile_memory:
            row_values.extend(
                [
                    # CPU Mem Total
                    _format_memory(evt.cpu_memory_usage),
                    # Self CPU Mem Total
                    _format_memory(evt.self_cpu_memory_usage),
                ]
            )
            if use_device and has_device_mem:
                row_values.extend(
                    [
                        # Device Mem Total
                        _format_memory(evt.device_memory_usage),
                        # Self Device Mem Total
                        _format_memory(evt.self_device_memory_usage),
                    ]
                )
        row_values.append(
            evt.count,  # Number of calls
        )

        if append_node_id:
            row_values.append(evt.node_id)
        if has_input_shapes:
            row_values.append(str(evt.input_shapes)[:shapes_column_width])
        if with_flops:
            if evt.flops <= 0:
                row_values.append("--")
            else:
                row_values.append(f"{evt.flops * flops_scale:8.3f}")  # type: ignore[possibly-undefined]
        if has_stack:
            src_field = ""
            if len(evt.stack) > 0:
                src_field = trim_path(evt.stack[0], src_column_width)
            row_values.append(src_field)
        append(row_format.format(*row_values))

        if has_stack:
            empty_headers = [""] * (len(headers) - 1)
            for entry in evt.stack[1:]:
                append(
                    row_format.format(
                        *(empty_headers + [trim_path(entry, src_column_width)])
                    )
                )
            empty_headers.append("")
            append(row_format.format(*empty_headers))

    append(header_sep)
    append(
        f"Self CPU time total: {override_time_unit(sum_self_cpu_time_total, _format_time(sum_self_cpu_time_total), time_unit)}"
    )
    if has_device_time:
        append(
            f"Self {use_device.upper() if use_device is not None else 'None'} "
            f"time total: {override_time_unit(sum_self_device_time_total, _format_time(sum_self_device_time_total), time_unit)}"
        )
    return "".join(result)