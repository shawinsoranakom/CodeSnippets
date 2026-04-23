def process_subsystem(
        cls,
        curr_backend: str,
        curr_subsystem: Subsystem,
        fn: Callable[[], bool],
        cli_interface: bool = True,
    ) -> bool:
        """
        Process the current subsystem. Returns True if the issue is found, False otherwise.
        """
        assert isinstance(curr_subsystem, Subsystem)
        while True:
            run_state = cls.get_run_state(curr_backend, curr_subsystem.name)
            reset_counters()
            if run_state == "test_disable":
                if not fn():
                    next_subsystem = cls.advance_subsystem(curr_backend, curr_subsystem)
                    if not next_subsystem:
                        return False
                    curr_subsystem = next_subsystem
                else:
                    if isinstance(curr_subsystem, ConfigChange):
                        print(
                            f"Setting config {curr_subsystem.config_name} field {curr_subsystem.config_field} "
                            f"to {curr_subsystem.config_value} fixed the issue"
                        )
                    else:
                        print(f"Disabling {curr_subsystem.name} fixed the issue.")
                    if isinstance(curr_subsystem, BinarySubsystem):
                        return True
                    print("Starting bisect by getting upper bound.")
                    cls.update_run_state(
                        curr_backend, curr_subsystem, "find_max_bounds"
                    )
            elif run_state == "find_max_bounds":
                if fn():
                    raise RuntimeError(
                        f"Function succeeded with 'find_max_bounds' status for {curr_backend} - {curr_subsystem.name}."
                    )
                else:
                    _, high = cls.get_bisect_range(curr_backend, curr_subsystem.name)
                    print(f"Upper bound of {high} found for {curr_backend}.")
                    cls.update_run_state(curr_backend, curr_subsystem, "bisect")
            elif run_state == "bisect":
                low, high = cls.get_bisect_range(curr_backend, curr_subsystem.name)
                midpoint = (low + high) // 2
                print(
                    f"Bisecting {curr_backend} - {curr_subsystem.name} (Range: [{low}, {high}], Midpoint: {midpoint})"
                )
                if fn():
                    cls.update_bisect_range(
                        curr_backend, curr_subsystem.name, midpoint + 1, high
                    )
                else:
                    cls.update_bisect_range(
                        curr_backend, curr_subsystem.name, low, midpoint
                    )
                low, high = cls.get_bisect_range(curr_backend, curr_subsystem.name)
                if low == high:
                    print(
                        f"Binary search completed for {curr_backend} - {curr_subsystem.name}. The bisect number is {low}. "
                        f"Debug info: {call_counter_debug_info.get(low, 'not found')}"
                    )
                    return True
            else:
                raise RuntimeError(f"Unexpected run_state {run_state}")

            if cli_interface:
                sys.exit(0)