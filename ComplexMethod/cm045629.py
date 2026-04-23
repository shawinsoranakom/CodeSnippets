def wait_result_with_checker(
    checker: Callable[[], bool],
    timeout_sec: float,
    *,
    step: float = 0.1,
    double_check_interval: float | None = None,
    target: Callable[..., None] | None = run,
    processes: int = 1,
    first_port: int | None = None,
    args: Iterable[Any] = (),
    kwargs: Mapping[str, Any] = {},
) -> None:
    handles: list[multiprocessing.Process] = []
    try:
        if target is not None:
            assert (
                multiprocessing.get_start_method() == "fork"
            ), "multiprocessing does not use fork(), pw.run() will not work"

            if processes != 1:
                assert first_port is not None
                run_id = uuid.uuid4()

                def target_wrapped(process_id, *args, **kwargs):
                    os.environ["PATHWAY_PROCESSES"] = str(processes)
                    os.environ["PATHWAY_FIRST_PORT"] = str(first_port)
                    os.environ["PATHWAY_PROCESS_ID"] = str(process_id)
                    os.environ["PATHWAY_RUN_ID"] = str(run_id)
                    target(*args, **kwargs)

                for process_id in range(processes):
                    p = multiprocessing.Process(
                        target=target_wrapped, args=(process_id, *args), kwargs=kwargs
                    )
                    p.start()
                    handles.append(p)
            else:
                target_wrapped = target
                p = multiprocessing.Process(target=target, args=args, kwargs=kwargs)
                p.start()
                handles.append(p)

        succeeded = False
        start_time = time.monotonic()
        while True:
            time.sleep(step)

            elapsed = time.monotonic() - start_time
            if elapsed >= timeout_sec:
                print("Timed out", file=sys.stderr)
                break

            succeeded = checker()
            if succeeded:
                print(
                    f"Correct result obtained after {elapsed:.1f} seconds",
                    file=sys.stderr,
                )
                if double_check_interval is not None:
                    time.sleep(double_check_interval)
                    succeeded = checker()
                    if not succeeded:
                        print("Double check failed.", file=sys.stderr)
                break

            if target is not None and not any(handle.is_alive() for handle in handles):
                print(
                    f"All processes are done in {elapsed} seconds",
                    file=sys.stderr,
                )
                assert all(handle.exitcode == 0 for handle in handles)
                break

        if not succeeded:
            provide_information_on_failure: Callable[[], str] | None = getattr(
                checker, "provide_information_on_failure", None
            )
            if provide_information_on_failure is not None:
                details = provide_information_on_failure()
            else:
                details = "(no details)"
            print(f"Checker failed: {details}", file=sys.stderr)
            raise AssertionError(details)
    finally:
        if target is not None:
            if "persistence_config" in kwargs:
                time.sleep(5.0)  # allow a little gap to persist state

            for p in handles:
                p.terminate()
                p.join()