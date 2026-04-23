def _runtest_env_changed_exc(result: TestResult, runtests: RunTests,
                             display_failure: bool = True) -> None:
    # Handle exceptions, detect environment changes.
    stdout = get_colors(file=sys.stdout)
    stderr = get_colors(file=sys.stderr)

    # Reset the environment_altered flag to detect if a test altered
    # the environment
    support.environment_altered = False

    pgo = runtests.pgo
    if pgo:
        display_failure = False
    quiet = runtests.quiet

    test_name = result.test_name
    try:
        clear_caches()
        support.gc_collect()

        with saved_test_environment(test_name,
                                    runtests.verbose, quiet, pgo=pgo):
            _load_run_test(result, runtests)
    except support.ResourceDenied as exc:
        if not quiet and not pgo:
            print(
                f"{stdout.YELLOW}{test_name} skipped -- {exc}{stdout.RESET}",
                flush=True,
            )
        result.state = State.RESOURCE_DENIED
        return
    except unittest.SkipTest as exc:
        if not quiet and not pgo:
            print(
                f"{stdout.YELLOW}{test_name} skipped -- {exc}{stdout.RESET}",
                flush=True,
            )
        result.state = State.SKIPPED
        return
    except support.TestFailedWithDetails as exc:
        msg = f"{stderr.RED}test {test_name} failed{stderr.RESET}"
        if display_failure:
            msg = f"{stderr.RED}{msg} -- {exc}{stderr.RESET}"
        print(msg, file=sys.stderr, flush=True)
        result.state = State.FAILED
        result.errors = exc.errors
        result.failures = exc.failures
        result.stats = exc.stats
        return
    except support.TestFailed as exc:
        msg = f"{stderr.RED}test {test_name} failed{stderr.RESET}"
        if display_failure:
            msg = f"{stderr.RED}{msg} -- {exc}{stderr.RESET}"
        print(msg, file=sys.stderr, flush=True)
        result.state = State.FAILED
        result.stats = exc.stats
        return
    except support.TestDidNotRun:
        result.state = State.DID_NOT_RUN
        return
    except KeyboardInterrupt:
        print()
        result.state = State.INTERRUPTED
        return
    except:
        if not pgo:
            msg = traceback.format_exc()
            print(
                f"{stderr.RED}test {test_name} crashed -- {msg}{stderr.RESET}",
                file=sys.stderr,
                flush=True,
            )
        result.state = State.UNCAUGHT_EXC
        return

    if support.environment_altered:
        result.set_env_changed()
    # Don't override the state if it was already set (REFLEAK or ENV_CHANGED)
    if result.state is None:
        result.state = State.PASSED