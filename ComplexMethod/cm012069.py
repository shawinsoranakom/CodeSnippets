def __init__(
        self,
        compiler: str = "",
        definitions: list[str] | None = None,
        include_dirs: list[str] | None = None,
        cflags: list[str] | None = None,
        ldflags: list[str] | None = None,
        libraries_dirs: list[str] | None = None,
        libraries: list[str] | None = None,
        passthrough_args: list[str] | None = None,
        aot_mode: bool = False,
        use_relative_path: bool = False,
        compile_only: bool = False,
        precompiling: bool = False,
        preprocessing: bool = False,
    ) -> None:
        self._compiler = compiler
        self._definitions: list[str] = definitions or []
        self._include_dirs: list[str] = include_dirs or []
        self._cflags: list[str] = cflags or []
        self._ldflags: list[str] = ldflags or []
        self._libraries_dirs: list[str] = libraries_dirs or []
        self._libraries: list[str] = libraries or []
        # Some args are hard to abstract to OS compatible, passthrough directly.
        self._passthrough_args: list[str] = passthrough_args or []

        # Optionally, the path to a precompiled header which should be included on the
        # build command line.
        self.precompiled_header: str | None = None

        self._aot_mode: bool = aot_mode
        self._use_relative_path: bool = use_relative_path
        self._compile_only: bool = compile_only
        self._precompiling: bool = precompiling
        self._preprocessing: bool = preprocessing