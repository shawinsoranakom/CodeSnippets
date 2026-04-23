def main():
    """Main benchmark function"""
    colors = get_colors(can_colorize())
    args = parse_arguments()

    print(f"{colors.BOLD_MAGENTA}External Inspection Benchmark Tool{colors.RESET}")
    print(f"{colors.BOLD_MAGENTA}{'=' * 34}{colors.RESET}")

    example_info = CODE_EXAMPLES.get(args.code, {"description": "Unknown"})
    print(
        f"\n{colors.CYAN}Code Example:{colors.RESET} {colors.GREEN}{args.code}{colors.RESET}"
    )
    print(f"{colors.CYAN}Description:{colors.RESET} {example_info['description']}")
    print(
        f"{colors.CYAN}Benchmark Duration:{colors.RESET} {colors.YELLOW}{args.duration}{colors.RESET} seconds"
    )
    print(
        f"{colors.CYAN}Blocking Mode:{colors.RESET} {colors.GREEN if args.blocking else colors.YELLOW}{'enabled' if args.blocking else 'disabled'}{colors.RESET}"
    )

    process = None
    temp_file_path = None

    try:
        # Create target process
        print(f"\n{colors.BLUE}Creating and starting target process...{colors.RESET}")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py") as temp_file:
            process, temp_file_path = create_target_process(temp_file, args.code)
            print(
                f"{colors.GREEN}Target process started with PID: {colors.BOLD_WHITE}{process.pid}{colors.RESET}"
            )

            # Run benchmark with specified duration
            with process:
                # Create unwinder and run benchmark
                print(f"{colors.BLUE}Initializing unwinder...{colors.RESET}")
                try:
                    kwargs = {}
                    if args.threads == "all":
                        kwargs["all_threads"] = True
                    elif args.threads == "main":
                        kwargs["all_threads"] = False
                    elif args.threads == "only_active":
                        kwargs["only_active_thread"] = True
                    unwinder = _remote_debugging.RemoteUnwinder(
                        process.pid, cache_frames=True, **kwargs
                    )
                    results = benchmark(unwinder, duration_seconds=args.duration, blocking=args.blocking)
                finally:
                    cleanup_process(process, temp_file_path)

            # Print results
            print_benchmark_results(results)

    except PermissionError as e:
        print(
            f"{colors.BOLD_RED}Error: Insufficient permissions to read stack trace: {e}{colors.RESET}"
        )
        print(
            f"{colors.YELLOW}Try running with appropriate privileges (e.g., sudo){colors.RESET}"
        )
        return 1
    except Exception as e:
        print(f"{colors.BOLD_RED}Error during benchmarking: {e}{colors.RESET}")
        if process:
            with contextlib.suppress(Exception):
                stdout, stderr = process.communicate(timeout=1)
                if stdout:
                    print(
                        f"{colors.CYAN}Process STDOUT:{colors.RESET} {stdout.decode()}"
                    )
                if stderr:
                    print(
                        f"{colors.RED}Process STDERR:{colors.RESET} {stderr.decode()}"
                    )
        raise

    return 0