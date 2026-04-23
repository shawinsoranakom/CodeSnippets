def worker_process(worker_json: StrJSON) -> NoReturn:
    runtests = WorkerRunTests.from_json(worker_json)
    test_name = runtests.tests[0]
    match_tests: TestFilter = runtests.match_tests
    json_file: JsonFile = runtests.json_file

    setup_test_dir(runtests.test_dir)
    setup_process()

    if runtests.rerun:
        if match_tests:
            matching = "matching: " + ", ".join(pattern for pattern, result in match_tests if result)
            print(f"Re-running {test_name} in verbose mode ({matching})", flush=True)
        else:
            print(f"Re-running {test_name} in verbose mode", flush=True)

    result = run_single_test(test_name, runtests)
    if runtests.coverage:
        if "test.cov" in sys.modules:  # imported by -Xpresite=
            result.covered_lines = list(sys.modules["test.cov"].coverage)
        elif not Py_DEBUG:
            print(
                "Gathering coverage in worker processes requires --with-pydebug",
                flush=True,
            )
        else:
            raise LookupError(
                "`test.cov` not found in sys.modules but coverage wanted"
            )

    if json_file.file_type == JsonFileType.STDOUT:
        print()
        result.write_json_into(sys.stdout)
    else:
        with json_file.open('w', encoding='utf-8') as json_fp:
            result.write_json_into(json_fp)

    sys.exit(0)