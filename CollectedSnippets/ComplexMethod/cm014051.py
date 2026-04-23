def _maybe_subprocess_run(
        self, args: Sequence[Any], *, isolate: bool, cwd: str | None = None
    ) -> subprocess.CompletedProcess[bytes]:
        from torch._inductor.cpp_builder import normalize_path_separator

        if not isolate:
            assert len(args) >= 2, args
            assert args[0] == "python3", args
            if args[1] == "-c":
                assert len(args) == 3, args
                code = args[2]
                args = ["-c"]
            else:
                assert len(args) >= 2, args
                with open(args[1]) as f:
                    # Need normalize path of the code.
                    code = normalize_path_separator(f.read())
                args = args[1:]

            # WARNING: This is not a perfect simulation of running
            # the program out of tree.  We only interpose on things we KNOW we
            # need to handle for tests.  If you need more stuff, you will
            # need to augment this appropriately.

            # NB: Can't use save_config because that will omit some fields,
            # but we must save and reset ALL fields
            dynamo_config = torch._dynamo.config.get_config_copy()
            inductor_config = torch._inductor.config.get_config_copy()
            try:
                stderr = io.StringIO()
                log_handler = logging.StreamHandler(stderr)
                log = logging.getLogger("torch._dynamo")
                log.addHandler(log_handler)
                try:
                    prev_cwd = _as_posix_path(os.getcwd())
                    if cwd is not None:
                        cwd = _as_posix_path(cwd)
                        os.chdir(cwd)
                    with patch("sys.argv", args), report_compile_source_on_error():
                        exec(code, {"__name__": "__main__", "__compile_source__": code})
                    rc = 0
                except Exception:
                    rc = 1
                    traceback.print_exc(file=stderr)
                finally:
                    log.removeHandler(log_handler)
                    if cwd is not None:
                        os.chdir(prev_cwd)  # type: ignore[possibly-undefined]
                    # Make sure we don't leave buggy compiled frames lying
                    # around
                    torch._dynamo.reset()
            finally:
                torch._dynamo.config.load_config(dynamo_config)
                torch._inductor.config.load_config(inductor_config)

            # TODO: return a more appropriate data structure here
            return subprocess.CompletedProcess(
                args,
                rc,
                b"",
                stderr.getvalue().encode("utf-8"),
            )
        else:
            if cwd is not None:
                cwd = _as_posix_path(cwd)
            return subprocess.run(args, capture_output=True, cwd=cwd, check=False)