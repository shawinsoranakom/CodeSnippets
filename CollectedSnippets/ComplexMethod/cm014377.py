def __init__(self) -> None:
        self._bindings_module: CallgrindModuleType | None = None
        valgrind_symbols = (
            "_valgrind_supported_platform",
            "_valgrind_toggle",
            "_valgrind_toggle_and_dump_stats",
        )
        if all(hasattr(torch._C, symbol) for symbol in valgrind_symbols):
            self._supported_platform: bool = torch._C._valgrind_supported_platform()

        else:
            print("Callgrind bindings are not present in `torch._C`. JIT-ing bindings.")
            self._bindings_module = cpp_jit.get_compat_bindings()
            if not all(hasattr(self._bindings_module, symbol) for symbol in valgrind_symbols):
                raise AssertionError("JIT-compiled callgrind bindings are missing required symbols")
            self._supported_platform = self._bindings_module._valgrind_supported_platform()

        self._commands_available: dict[str, bool] = {}
        if self._supported_platform:
            # Only bother checking on supported platforms.
            for cmd in ("valgrind", "callgrind_control", "callgrind_annotate"):
                self._commands_available[cmd] = not subprocess.run(
                    ["which", cmd],
                    capture_output=True,
                    check=False,
                ).returncode

        self._build_type: str | None = None
        build_search = re.search("BUILD_TYPE=(.+),", torch.__config__.show())  # type: ignore[no-untyped-call]
        if build_search is not None:
            self._build_type = build_search.groups()[0].split(",")[0]