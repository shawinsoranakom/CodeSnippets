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