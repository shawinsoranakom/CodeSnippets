def fp8_bench(fn: Callable[[], Any], warmup: int = 25, rep: int = 100) -> float:
    """
    Returns benchmark results by examining torch profiler events.
    This could be more accurate as it doesn't count CPU side overhead.
    However, this also requires manually excluding irrelevant event, e.g.
    vectorized_elementwise_kernel which is used to fill L2 cache,
    various CUDA events, etc, so could also be fragile.
    """

    fn()
    torch.cuda.synchronize()
    cache = torch.empty(int(256e6 // 4), dtype=torch.float16, device="cuda")

    # Estimate the runtime of the function
    start_event = torch.cuda.Event(enable_timing=True)
    end_event = torch.cuda.Event(enable_timing=True)
    start_event.record()
    for _ in range(5):
        cache.zero_()
        fn()
    end_event.record()
    torch.cuda.synchronize()
    estimate_ms = start_event.elapsed_time(end_event) / 5

    # compute number of warmup and repeat
    n_warmup = max(1, int(warmup / estimate_ms))
    n_repeat = max(1, int(rep / estimate_ms))

    # Warm-up
    for _ in range(n_warmup):
        fn()

    start_event = [torch.cuda.Event(enable_timing=True) for _ in range(n_repeat)]
    end_event = [torch.cuda.Event(enable_timing=True) for _ in range(n_repeat)]
    with torch.profiler.profile(
        activities=[
            torch.profiler.ProfilerActivity.CUDA,
        ]
    ) as p:
        torch.cuda.synchronize()
        for i in range(n_repeat):
            cache.zero_()
            start_event[i].record()
            with torch.cuda.nvtx.range("RunCudaModule"):
                fn()
            end_event[i].record()
        torch.cuda.synchronize()
        times = torch.tensor(
            [s.elapsed_time(e) for s, e in zip(start_event, end_event)]
        )

    res = torch.mean(times).item()
    log.debug("raw events")
    log.debug(p.key_averages().table(sort_by="self_device_time_total", row_limit=-1))
    filtered_events = EventList(
        [
            event
            for event in p.events()
            if (
                event.device_type == DeviceType.CUDA
                and re.match(r"fused_abs_max_\d", event.name) is not None
            )
        ]
    )
    if filtered_events:
        res -= (
            statistics.mean(event.device_time_total for event in filtered_events)
            / 1000.0
        )

    log.debug("profiling results: %s ms", res)
    return res