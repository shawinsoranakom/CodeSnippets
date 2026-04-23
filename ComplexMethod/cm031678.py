def benchmark(unwinder, duration_seconds=10, blocking=False):
    """Benchmark mode - measure raw sampling speed for specified duration"""
    sample_count = 0
    fail_count = 0
    total_work_time = 0.0
    start_time = time.perf_counter()
    end_time = start_time + duration_seconds
    total_attempts = 0

    colors = get_colors(can_colorize())

    print(
        f"{colors.BOLD_BLUE}Benchmarking sampling speed for {duration_seconds} seconds...{colors.RESET}"
    )

    try:
        while time.perf_counter() < end_time:
            total_attempts += 1
            work_start = time.perf_counter()
            try:
                if blocking:
                    unwinder.pause_threads()
                try:
                    stack_trace = unwinder.get_stack_trace()
                    if stack_trace:
                        sample_count += 1
                finally:
                    if blocking:
                        unwinder.resume_threads()
            except (OSError, RuntimeError, UnicodeDecodeError) as e:
                fail_count += 1

            work_end = time.perf_counter()
            total_work_time += work_end - work_start

            if total_attempts % 10000 == 0:
                avg_work_time_us = (total_work_time / total_attempts) * 1e6
                work_rate = (
                    total_attempts / total_work_time if total_work_time > 0 else 0
                )
                success_rate = (sample_count / total_attempts) * 100

                # Color code the success rate
                if success_rate >= 95:
                    success_color = colors.GREEN
                elif success_rate >= 80:
                    success_color = colors.YELLOW
                else:
                    success_color = colors.RED

                print(
                    f"{colors.CYAN}Attempts:{colors.RESET} {total_attempts} | "
                    f"{colors.CYAN}Success:{colors.RESET} {success_color}{success_rate:.1f}%{colors.RESET} | "
                    f"{colors.CYAN}Rate:{colors.RESET} {colors.MAGENTA}{work_rate:.1f}Hz{colors.RESET} | "
                    f"{colors.CYAN}Avg:{colors.RESET} {colors.YELLOW}{avg_work_time_us:.2f}µs{colors.RESET}"
                )
    except KeyboardInterrupt:
        print(f"\n{colors.YELLOW}Benchmark interrupted by user{colors.RESET}")

    actual_end_time = time.perf_counter()
    wall_time = actual_end_time - start_time

    # Return final statistics
    return {
        "wall_time": wall_time,
        "total_attempts": total_attempts,
        "sample_count": sample_count,
        "fail_count": fail_count,
        "success_rate": (
            (sample_count / total_attempts) * 100 if total_attempts > 0 else 0
        ),
        "total_work_time": total_work_time,
        "avg_work_time_us": (
            (total_work_time / total_attempts) * 1e6 if total_attempts > 0 else 0
        ),
        "work_rate_hz": total_attempts / total_work_time if total_work_time > 0 else 0,
        "samples_per_sec": sample_count / wall_time if wall_time > 0 else 0,
    }