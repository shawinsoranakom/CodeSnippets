def _runtest(result: TestResult, runtests: RunTests) -> None:
    # Capture stdout and stderr, set faulthandler timeout,
    # and create JUnit XML report.
    verbose = runtests.verbose
    output_on_failure = runtests.output_on_failure
    timeout = runtests.timeout

    if timeout is not None and threading_helper.can_start_thread:
        use_timeout = True
        faulthandler.dump_traceback_later(timeout, exit=True)
    else:
        use_timeout = False

    try:
        setup_tests(runtests)

        if output_on_failure or runtests.pgo:
            support.verbose = True

            stream = io.StringIO()
            orig_stdout = sys.stdout
            orig_stderr = sys.stderr
            print_warning = support.print_warning
            orig_print_warnings_stderr = print_warning.orig_stderr

            output = None
            try:
                sys.stdout = stream
                sys.stderr = stream
                # print_warning() writes into the temporary stream to preserve
                # messages order. If support.environment_altered becomes true,
                # warnings will be written to sys.stderr below.
                print_warning.orig_stderr = stream

                _runtest_env_changed_exc(result, runtests, display_failure=False)
                # Ignore output if the test passed successfully
                if result.state != State.PASSED:
                    output = stream.getvalue()
            finally:
                sys.stdout = orig_stdout
                sys.stderr = orig_stderr
                print_warning.orig_stderr = orig_print_warnings_stderr

            if output is not None:
                sys.stderr.write(output)
                sys.stderr.flush()
        else:
            # Tell tests to be moderately quiet
            support.verbose = verbose
            _runtest_env_changed_exc(result, runtests,
                                     display_failure=not verbose)

        xml_list = support.junit_xml_list
        if xml_list:
            result.xml_data = xml_list
    finally:
        if use_timeout:
            faulthandler.cancel_dump_traceback_later()
        support.junit_xml_list = None