def command_line_usage() -> None:
    """Entry point for the compiler bisector command-line interface."""
    if len(sys.argv) < 2:
        print(HELP_TEXT)
        sys.exit(1)

    bisection_manager = CompilerBisector()
    command = sys.argv[1]

    if command == "end":
        bisection_manager.delete_bisect_status()
        sys.exit(0)

    if command == "start":
        bisection_manager.delete_bisect_status()
        bisection_manager.initialize_system()
        sys.exit(0)

    if command == "run":
        if len(sys.argv) < 3:
            print(
                "Usage: python -m torch._inductor.compiler_bisector run <command> [args...]"
            )
            sys.exit(1)

        import subprocess

        run_cmd = sys.argv[2:]

        def test_function() -> bool:
            # Pass bisection state to subprocess via environment variables
            env = os.environ.copy()
            backend = bisection_manager.get_backend()
            subsystem = bisection_manager.get_subsystem()

            if backend:
                # For test script to select the right backend
                env["TORCH_COMPILE_BACKEND"] = backend
                # For bisector in subprocess to know which backend we're testing
                env["TORCH_BISECT_BACKEND"] = backend

            if subsystem:
                assert backend is not None  # subsystem requires a backend
                env["TORCH_BISECT_SUBSYSTEM"] = subsystem
                # Get run_state to determine TORCH_BISECT_MAX
                run_state = bisection_manager.get_run_state(backend, subsystem)
                if run_state == "test_disable":
                    # -1 means always disable (counter > -1 is always True)
                    env["TORCH_BISECT_MAX"] = "-1"
                # For find_max_bounds and bisect, let the subprocess use file-based
                # mechanisms. The subprocess reads run_state and bisect_range from
                # files, and writes the actual count during find_max_bounds.

            result = subprocess.run(run_cmd, env=env)
            return result.returncode == 0

        bisection_manager.delete_bisect_status()
        bisection_manager.bisection_enabled = True
        # Use shared cache_dir instead of temp dir so subprocesses can access files
        CompilerBisector.in_process_cache = cache_dir()
        result = bisection_manager.do_bisect(test_function, cli_interface=False)
        if result:
            print(f"\nBisection complete: {result}")
        else:
            print("\nBisection complete: no issue found")
        sys.exit(0)

    if command not in ["good", "bad"]:
        print(f"Invalid command: {command}")
        print("Must be 'good', 'bad', 'start', 'end', or 'run'.")
        sys.exit(1)

    def test_function() -> bool:
        return command == "good"

    if not bisection_manager.get_backend():
        raise ValueError("Must call start prior to good or bad")

    bisection_manager.do_bisect(test_function, cli_interface=True)