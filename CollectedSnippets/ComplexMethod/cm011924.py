def make_precompile_fn(
        self,
        choices,
        name: str,
        inputs_key: str,
        precompilation_timeout_seconds: int | None = 60 * 60,
    ) -> Callable[[], dict[ChoiceCaller, float]]:
        """
        Returns a function that precompiles the given choices.
        """
        log.debug("Starting precompilation")

        def no_op(*args, **kwargs) -> dict[ChoiceCaller, float]:
            return {}

        if (
            precompilation_timeout_seconds is None
            or precompilation_timeout_seconds <= 0
        ):
            log.debug("Precompilation timeout is None or <= 0, returning no_op")
            return no_op

        num_workers = min(get_num_workers(), len(choices))

        if num_workers <= 0:
            return no_op

        # https://github.com/python/cpython/issues/106905
        if (
            sys.version_info.major == 3
            and sys.version_info.minor == 11
            and sys.version_info.micro <= 8
        ):
            return no_op

        # check local and global cache before precompiling
        timings = self.lookup(
            choices,
            name,
            inputs_key,
            benchmark=None,
        )

        if timings and len(timings) == len(choices):
            # compilation in precompile stage is much cheaper than that in
            # autotuning stage
            log.debug("Found all %d timings in cache, returning no_op", len(timings))
            return no_op

        precompile_key = create_precompile_key(name, inputs_key, choices)
        if precompile_func := self.precompile_cache.get(precompile_key):
            log.debug("Precompile function found in cache, returning it")
            return precompile_func

        log.info(
            "Multithreaded precompilation for %d choices using %d worker threads",
            len(choices),
            num_workers,
        )

        # In rare circumstances, because python threads inherit global state,
        # thread pool executor can race and leave stdout/stderr in a state
        # different than the original values. we explicitly restore the state
        # here to avoid this issue.

        def precompile_with_captured_stdout(choice) -> tuple[None, int]:
            log.debug("Precompiling choice with captured stdout: %s", choice)
            start_ns = time.time_ns()
            with restore_stdout_stderr():
                choice.precompile()
            elapsed_ns = time.time_ns() - start_ns
            # Return tuple as triton async compile (_worker_compile_triton)
            # returns tuple[CachingAutotuner, int]
            return None, elapsed_ns // 1000

        def on_complete(future):
            if not future.exception():
                _, precompile_elapsed_us = future.result()
                elapsed_seconds = precompile_elapsed_us / 1e6
                elapsed_times[future] = elapsed_seconds
                log.debug(
                    "Precompilation complete for future: %s, elapsed time: %.02fs",
                    future,
                    elapsed_seconds,
                )

        if use_pipelined_autotuning():
            executor = PrecompileThreadPool.get_instance()
        else:
            executor = ThreadPoolExecutor(max_workers=num_workers)

        async_compile = torch._inductor.async_compile.AsyncCompile()

        futures: dict[concurrent.futures.Future[Any], ChoiceCaller] = {}
        elapsed_times: dict[concurrent.futures.Future[Any], float] = {}

        # Some choices only differ in runtime arguments, so we
        # skip a choice if it has the same hash as a previously seen choice
        seen_choices: OrderedSet[str] = OrderedSet()
        for c in choices:
            # Skip choices which we have already issued a precompile
            if c.kernel_hash_key() in seen_choices:
                log.debug("Skipping already seen choice: %s", c)
                continue
            else:
                seen_choices.add(c.kernel_hash_key())

            if hasattr(c, "precompile"):
                triton_cuda_choice = isinstance(c, TritonTemplateCaller) and isinstance(
                    c.bmreq, TritonGPUBenchmarkRequest
                )
                if triton_cuda_choice and async_compile.use_process_pool():
                    with open(c.bmreq.module_path) as file:
                        source_code = file.read()
                    future = async_compile.triton(
                        kernel_name=c.bmreq.kernel_name, source_code=source_code
                    ).future
                    log.debug("Submitted triton async compile for choice: %s", c)
                else:
                    future = executor.submit(precompile_with_captured_stdout, c)
                    log.debug("Submitted precompile for choice: %s", c)

                future.add_done_callback(on_complete)
                futures[future] = c

        @functools.cache
        @restore_stdout_stderr()
        def wait_on_futures() -> dict[ChoiceCaller, float]:
            """Wait for all precompilation futures to complete.

            Returns:
                Dict mapping each choice to its precompilation time in seconds.
            """
            log.debug("Waiting on futures")
            counters["inductor"]["select_algorithm_precompile"] += 1
            exceptions: list[tuple[ChoiceCaller, BaseException]] = []
            try:
                for future in as_completed(
                    futures,
                    timeout=precompilation_timeout_seconds,
                ):
                    if e := future.exception():
                        counters["inductor"][
                            "select_algorithm_num_precompilation_exceptions"
                        ] += 1
                        exceptions.append((futures[future], e))
                        log.exception(
                            "Exception %s for benchmark choice %s",
                            e,
                            futures[future],
                            exc_info=e,
                        )
                        futures[future].mark_failed()
                    else:
                        counters["inductor"]["select_algorithm_num_precompiles"] += 1
                        log.info(
                            "Precompiling benchmark choice %s took %.02fs",
                            futures.get(future),
                            elapsed_times.get(future),
                        )
            except TimeoutError:
                # Don't force the entire process to crash due to a timeout
                # in compilation. Just mark those futures as failed.
                completed_futures = OrderedSet([f for f in futures if f.done()])
                remaining_futures = OrderedSet(futures.keys()) - completed_futures

                log.warning(
                    "Precompilation timeout after %ds: %d of %d futures did not complete",
                    precompilation_timeout_seconds,
                    len(remaining_futures),
                    len(futures),
                )

                # Mark remaining futures as failed and log them
                for future in remaining_futures:
                    choice = futures[future]
                    log.warning(
                        "Marking choice as failed due to timeout: %s",
                        choice,
                    )
                    choice.mark_failed()
                    # Add timeout exception to the exceptions list
                    timeout_exc = TimeoutError(
                        f"Precompilation timed out after {precompilation_timeout_seconds}s"
                    )
                    exceptions.append((choice, timeout_exc))
            if exceptions:
                _log_autotune_exceptions(exceptions)

            if not use_pipelined_autotuning():
                # pyrefly: ignore [missing-attribute]
                executor.shutdown(wait=True)

            # Build and return dict mapping choices to their precompilation times
            precompile_times: dict[ChoiceCaller, float] = {}
            for future, choice in futures.items():
                if future in elapsed_times:
                    precompile_times[choice] = elapsed_times[future]
            return precompile_times

        self.precompile_cache[precompile_key] = wait_on_futures

        return wait_on_futures