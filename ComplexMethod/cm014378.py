def _invoke(
        self,
        *,
        task_spec: common.TaskSpec,
        globals: dict[str, Any],
        number: int,
        repeats: int,
        collect_baseline: bool,
        is_python: bool,
        retain_out_file: bool,
    ) -> tuple[tuple[FunctionCounts, FunctionCounts, str | None], ...]:
        """Core invocation method for Callgrind collection.

        Valgrind operates by effectively replacing the CPU with an emulated
        version which allows it to instrument any code at the cost of severe
        performance degradation. This has the practical effect that in order
        to collect Callgrind statistics, a new process has to be created
        running under `valgrind`. The steps for this process are:

        1) Create a scratch directory.
        2) Codegen a run script. (_ValgrindWrapper._construct_script)
            Inside the run script:
                * Validate that Python and torch match the parent process
                * Validate that it is indeed running under valgrind
                * Execute `setup` and warm up `stmt`
                * Begin collecting stats
                * Run the `stmt` loop
                * Stop collecting stats
        3) Parse the run results.
        4) Cleanup the scratch directory.
        """
        working_dir = common._make_temp_dir(prefix="callgrind")
        data_dir = os.path.join(working_dir, "data")
        script_file = os.path.join(working_dir, "timer_callgrind.py")
        callgrind_out = os.path.join(working_dir, "callgrind.out")
        error_log = os.path.join(working_dir, "error.txt")
        stat_log = os.path.join(working_dir, "callgrind_stat.txt")
        stdout_stderr_log = os.path.join(working_dir, "stdout_stderr.log")

        def run(args: list[str], **kwargs: Any) -> tuple[CompletedProcessType, str]:
            # https://thraxil.org/users/anders/posts/2008/03/13/Subprocess-Hanging-PIPE-is-your-enemy/
            with open(stdout_stderr_log, "wb") as f_stdout_stderr:
                invocation = subprocess.run(
                    args,
                    stdout=f_stdout_stderr,
                    stderr=subprocess.STDOUT,
                    **kwargs,
                )
                with open(stdout_stderr_log) as f:
                    return invocation, f.read()

        try:
            if is_python:
                if self._bindings_module is not None:
                    shutil.copy(
                        self._bindings_module.__file__,
                        os.path.join(working_dir, os.path.split(self._bindings_module.__file__)[1])
                    )

                script_file = os.path.join(working_dir, "timer_callgrind.py")
                with open(script_file, "w") as f:
                    f.write(self._construct_script(
                        task_spec,
                        globals=GlobalsBridge(globals, data_dir),
                        number=number,
                        repeats=repeats,
                        collect_baseline=collect_baseline,
                        error_log=error_log,
                        stat_log=stat_log,
                        bindings=self._bindings_module))

                run_loop_cmd = ["python", script_file]
            else:
                if collect_baseline:
                    raise AssertionError("collect_baseline must be False for non-Python timers")
                run_loop_exec = cpp_jit.compile_callgrind_template(
                    stmt=task_spec.stmt,
                    setup=task_spec.setup,
                    global_setup=task_spec.global_setup,
                )
                run_loop_cmd = [
                    run_loop_exec,
                    "--number", str(number),
                    "--number-warmup", str(min(number, 10)),
                    "--repeats", str(repeats),
                    "--number-threads", str(task_spec.num_threads),
                ]

            valgrind_invocation, valgrind_invocation_output = run([
                "valgrind",
                "--tool=callgrind",
                f"--callgrind-out-file={callgrind_out}",
                "--dump-line=yes",
                "--dump-instr=yes",
                "--instr-atstart=yes",
                "--collect-atstart=no",
            ] + run_loop_cmd)

            if valgrind_invocation.returncode:
                error_report = ""
                if os.path.exists(error_log):
                    with open(error_log) as f:
                        error_report = f.read()
                if not error_report:
                    error_report = "Unknown error.\n" + valgrind_invocation_output

                raise OSError(f"Failed to collect callgrind profile:\n{error_report}")

            def parse_output(fpath: str, inclusive: bool) -> FunctionCounts:
                _annotate_invocation, annotate_invocation_output = run([
                    "callgrind_annotate",
                    f"--inclusive={'yes' if inclusive else 'no'}",
                    "--threshold=100",
                    "--show-percs=no",
                    fpath
                ], check=True)

                total_pattern = re.compile(r"^([0-9,]+)\s+PROGRAM TOTALS")
                begin_pattern = re.compile(r"Ir\s+file:function")
                function_pattern = re.compile(r"^\s*([0-9,]+)\s+(.+:.+)$")

                class ScanState(enum.Enum):
                    SCANNING_FOR_TOTAL = 0
                    SCANNING_FOR_START = 1
                    PARSING = 2

                scan_state = ScanState.SCANNING_FOR_TOTAL
                fn_counts = []
                for l in annotate_invocation_output.splitlines(keepends=False):
                    if scan_state == ScanState.SCANNING_FOR_TOTAL:
                        total_match = total_pattern.match(l)
                        if total_match:
                            program_totals = int(total_match.groups()[0].replace(",", ""))
                            scan_state = ScanState.SCANNING_FOR_START

                    elif scan_state == ScanState.SCANNING_FOR_START:
                        if begin_pattern.match(l):
                            scan_state = ScanState.PARSING

                    else:
                        if scan_state != ScanState.PARSING:
                            raise AssertionError("Failed to enter PARSING state while parsing callgrind_annotate output")
                        fn_match = function_pattern.match(l)
                        if fn_match:
                            ir_str, file_function = fn_match.groups()
                            ir = int(ir_str.replace(",", ""))
                            if ir == program_totals:  # type: ignore[possibly-undefined]
                                # Callgrind includes some top level red herring symbols when
                                # a program dumps multiple profiles.
                                continue
                            fn_counts.append(FunctionCount(ir, file_function))

                        elif re.match(r"-+", l):
                            # Ignore heading separator lines.
                            continue

                        else:
                            break

                if scan_state != ScanState.PARSING:
                    raise AssertionError(f"Failed to parse {fpath}")
                return FunctionCounts(tuple(sorted(fn_counts, reverse=True)), inclusive=inclusive)

            def read_results(i: int) -> tuple[FunctionCounts, FunctionCounts, str | None]:
                if i == repeats and not collect_baseline:
                    # Null baseline.
                    return (
                        FunctionCounts((), inclusive=True),
                        FunctionCounts((), inclusive=False),
                        None,
                    )

                fpath = f"{callgrind_out}.{i + 1}"  # Callgrind one-indexes files.
                callgrind_out_contents: str | None = None
                if retain_out_file:
                    with open(fpath) as f:
                        callgrind_out_contents = f.read()

                return (
                    parse_output(fpath, inclusive=True),
                    parse_output(fpath, inclusive=False),
                    callgrind_out_contents
                )

            return tuple(read_results(i) for i in range(repeats + 1))
        finally:
            shutil.rmtree(working_dir)