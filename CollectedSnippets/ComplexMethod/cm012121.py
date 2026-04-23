def disable_subsystem(
        cls,
        backend: str,
        subsystem: str,
        debug_info: Callable[[], str] | None = None,
    ) -> bool:
        if not cls.bisection_enabled:
            return False

        if cls.get_backend() != backend:
            return False

        if cls.get_subsystem() != subsystem:
            return False

        if val := get_env_val("TORCH_BISECT_MAX"):
            counter = cls.get_system_counter(subsystem, increment=True)
            return counter > int(val)

        run_state = cls.get_run_state(backend, subsystem)
        if run_state == "test_disable":
            # First run, disable completely
            return True
        elif run_state == "find_max_bounds":
            # Second run, update bisection range and return True to enable the subsystem
            cls.update_bisect_range(
                backend,
                subsystem,
                0,
                cls.get_system_counter(subsystem, increment=True),
            )
            return False
        else:
            assert run_state == "bisect"
            # If the environment variable is not set, use the bisection range midpoint
            low, high = cls.get_bisect_range(backend, subsystem)
            # if high - low <= 2:
            midpoint = (low + high) // 2
            call_counter = cls.get_system_counter(subsystem)

            if (
                call_counter >= low
                and call_counter <= high
                and (low - high) <= 2
                and debug_info is not None
            ):
                call_counter_debug_info[call_counter] = debug_info()

            return call_counter > midpoint