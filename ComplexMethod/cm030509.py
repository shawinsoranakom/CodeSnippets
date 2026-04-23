def main() -> NoReturn:
    """
    Main coordinator function.

    This function coordinates the startup of a target Python process
    with the sample profiler by signaling when the process is ready
    to be profiled.
    """
    # Phase 1: Parse arguments and set up environment
    # Errors here are coordinator errors, not script errors
    try:
        # Parse and validate arguments
        sync_port, cwd, target_args = _validate_arguments(sys.argv)

        # Set up execution environment
        _setup_environment(cwd)

        # Determine execution type and validate target exists
        is_module = target_args[0] == "-m"
        if is_module:
            if len(target_args) < 2:
                raise ArgumentError("Module name required after -m")
            module_name = target_args[1]
            module_args = target_args[2:]

            if importlib.util.find_spec(module_name) is None:
                raise TargetError(f"Module not found: {module_name}")
        else:
            script_path = target_args[0]
            script_args = target_args[1:]
            # Match the path resolution logic in _execute_script
            check_path = script_path if os.path.isabs(script_path) else os.path.join(cwd, script_path)
            if not os.path.isfile(check_path):
                raise TargetError(f"Script not found: {script_path}")

        # Signal readiness to profiler
        _signal_readiness(sync_port)

    except CoordinatorError as e:
        print(f"Profiler coordinator error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        sys.exit(1)

    # Phase 2: Execute the target script/module
    # Let exceptions propagate naturally so Python prints full tracebacks
    if is_module:
        _execute_module(module_name, module_args)
    else:
        _execute_script(script_path, script_args, cwd)

    # Normal exit
    sys.exit(0)