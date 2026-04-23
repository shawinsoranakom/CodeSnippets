def do_bisect(
        cls, fn: Callable[[], bool], cli_interface: bool = False
    ) -> BisectionResult | None:
        """
        Run fn repeatedly attempting to bisect torch.compile. fn should return True on success and False on failure.
        """

        # TODO graph bisecting is not well composed with lowering
        # bisector so far. Use a config to opt-in
        import torch._inductor.config as inductor_config

        if inductor_config.test_configs.bisect_pre_grad_graph:
            BACKENDS["inductor"].insert(0, BisectSubsystem("pre_grad_graph"))

        if not cli_interface:
            bisection_enabled_orig = cls.bisection_enabled
            cls.delete_bisect_status()
            cls.bisection_enabled = True
            # Only create temp dir if not already set (CLI run mode pre-sets it)
            if not cls.in_process_cache:
                cls.in_process_cache = tempfile.mkdtemp()

            def cleanup() -> None:
                cls.bisection_enabled = bisection_enabled_orig
                cls.delete_bisect_status()
                cls.in_process_cache = None

                if BACKENDS["inductor"][0].name == "pre_grad_graph":
                    del BACKENDS["inductor"][0]

            cleanup_handler = atexit.register(cleanup)

            class DisableBisect:
                def __del__(self) -> None:
                    cleanup()
                    atexit.unregister(cleanup_handler)

            _cleanup = DisableBisect()

        curr_backend = cls.get_backend()
        curr_subsystem_name = cls.get_subsystem()

        if not curr_backend:
            cls.initialize_system()
            curr_backend = cls.get_backend()
            assert curr_backend is not None
            curr_subsystem_name = cls.get_subsystem()

        curr_subsystem = (
            cls.get_subsystem_object(curr_backend, curr_subsystem_name)
            if curr_subsystem_name is not None
            else None
        )
        while True:
            assert curr_backend is not None
            reset_counters()
            if curr_subsystem:
                result = cls.process_subsystem(
                    curr_backend, curr_subsystem, fn, cli_interface=cli_interface
                )
                if result:
                    curr_subsystem = cls.get_subsystem_object(
                        curr_backend,
                        cls.get_subsystem(),  # type: ignore[arg-type]
                    )

                    if isinstance(curr_subsystem, BinarySubsystem):
                        return BisectionResult(
                            curr_backend,
                            curr_subsystem.name,
                            0,
                            curr_subsystem.name,
                        )

                    low, _ = cls.get_bisect_range(curr_backend, curr_subsystem.name)
                    return BisectionResult(
                        curr_backend,
                        curr_subsystem.name,
                        low,
                        call_counter_debug_info.get(low),
                    )

                next_subsystem = cls.advance_subsystem(curr_backend, curr_subsystem)
                if not next_subsystem:
                    print(
                        f"The issue is in the {curr_backend} system, but could not identify subsystem."
                    )
                    assert curr_backend is not None
                    return BisectionResult(curr_backend)

                curr_subsystem = next_subsystem
            else:
                if fn():
                    next_backend = cls.advance_backend(curr_backend)
                    if not next_backend:
                        print("All systems have been checked.")
                        return None

                    curr_backend = next_backend
                else:
                    current_subsystems = BACKENDS[curr_backend]
                    if current_subsystems:
                        curr_subsystem = current_subsystems[0]
                        cls.update_bisect_status(curr_backend, curr_subsystem.name)
                        cls.update_run_state(
                            curr_backend, curr_subsystem, "test_disable"
                        )
                        print(
                            f"The issue is in the {curr_backend} system. Moving to the first subsystem: {curr_subsystem}"
                        )
                    else:
                        print(f"The issue is in the {curr_backend} system.")
                        return BisectionResult(curr_backend)

            if cli_interface:
                sys.exit(0)