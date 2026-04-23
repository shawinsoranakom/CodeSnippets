def copy_with(
        self,
        *,
        argparse: Argparse | None = None,
        difflib: Difflib | None = None,
        fancycompleter: FancyCompleter | None = None,
        http_server: HttpServer | None = None,
        live_profiler: LiveProfiler | None = None,
        syntax: Syntax | None = None,
        timeit: Timeit | None = None,
        traceback: Traceback | None = None,
        unittest: Unittest | None = None,
    ) -> Self:
        """Return a new Theme based on this instance with some sections replaced.

        Themes are immutable to protect against accidental modifications that
        could lead to invalid terminal states.
        """
        return type(self)(
            argparse=argparse or self.argparse,
            difflib=difflib or self.difflib,
            fancycompleter=fancycompleter or self.fancycompleter,
            http_server=http_server or self.http_server,
            live_profiler=live_profiler or self.live_profiler,
            syntax=syntax or self.syntax,
            timeit=timeit or self.timeit,
            traceback=traceback or self.traceback,
            unittest=unittest or self.unittest,
        )