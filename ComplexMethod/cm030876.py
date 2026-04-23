def main():
    args = parse_args()
    for opt in ('-w', '--rerun', '--verbose2'):
        if opt in args.test_args:
            print(f"WARNING: {opt} option should not be used to bisect!")
            print()

    if args.input:
        with open(args.input) as fp:
            tests = [line.strip() for line in fp]
    else:
        tests = list_cases(args)

    print("Start bisection with %s tests" % len(tests))
    print("Test arguments: %s" % format_shell_args(args.test_args))
    print("Bisection will stop when getting %s or less tests "
          "(-n/--max-tests option), or after %s iterations "
          "(-N/--max-iter option)"
          % (args.max_tests, args.max_iter))
    output = write_output(args.output, tests)
    print()

    start_time = time.monotonic()
    iteration = 1
    try:
        while len(tests) > args.max_tests and iteration <= args.max_iter:
            ntest = len(tests)
            ntest = max(ntest // 2, 1)
            subtests = random.sample(tests, ntest)

            print(f"[+] Iteration {iteration}/{args.max_iter}: "
                  f"run {len(subtests)} tests/{len(tests)}")
            print()

            exitcode = run_tests(args, subtests)

            print("ran %s tests/%s" % (ntest, len(tests)))
            print("exit", exitcode)
            if exitcode:
                print("Tests failed: continuing with this subtest")
                tests = subtests
                output = write_output(args.output, tests)
            else:
                print("Tests succeeded: skipping this subtest, trying a new subset")
            print()
            iteration += 1
    except KeyboardInterrupt:
        print()
        print("Bisection interrupted!")
        print()

    print("Tests (%s):" % len(tests))
    for test in tests:
        print("* %s" % test)
    print()

    if output:
        print("Output written into %s" % output)

    dt = math.ceil(time.monotonic() - start_time)
    if len(tests) <= args.max_tests:
        print("Bisection completed in %s iterations and %s"
              % (iteration, datetime.timedelta(seconds=dt)))
    else:
        print("Bisection failed after %s iterations and %s"
              % (iteration, datetime.timedelta(seconds=dt)))
        sys.exit(1)