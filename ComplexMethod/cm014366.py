def collect_callgrind(
        self,
        number: int = 100,
        *,
        repeats: int | None = None,
        collect_baseline: bool = True,
        retain_out_file: bool = False,
    ) -> Any:
        """Collect instruction counts using Callgrind.

        Unlike wall times, instruction counts are deterministic
        (modulo non-determinism in the program itself and small amounts of
        jitter from the Python interpreter.) This makes them ideal for detailed
        performance analysis. This method runs `stmt` in a separate process
        so that Valgrind can instrument the program. Performance is severely
        degraded due to the instrumentation, however this is ameliorated by
        the fact that a small number of iterations is generally sufficient to
        obtain good measurements.

        In order to use this method `valgrind`, `callgrind_control`, and
        `callgrind_annotate` must be installed.

        Because there is a process boundary between the caller (this process)
        and the `stmt` execution, `globals` cannot contain arbitrary in-memory
        data structures. (Unlike timing methods) Instead, globals are
        restricted to builtins, `nn.Modules`'s, and TorchScripted functions/modules
        to reduce the surprise factor from serialization and subsequent
        deserialization. The `GlobalsBridge` class provides more detail on this
        subject. Take particular care with nn.Modules: they rely on pickle and
        you may need to add an import to `setup` for them to transfer properly.

        By default, a profile for an empty statement will be collected and
        cached to indicate how many instructions are from the Python loop which
        drives `stmt`.

        Returns:
            A `CallgrindStats` object which provides instruction counts and
            some basic facilities for analyzing and manipulating results.
        """
        if not isinstance(self._task_spec.stmt, str):
            raise ValueError("`collect_callgrind` currently only supports string `stmt`")

        if repeats is not None and repeats < 1:
            raise ValueError("If specified, `repeats` must be >= 1")

        # Check that the statement is valid. It doesn't guarantee success, but it's much
        # simpler and quicker to raise an exception for a faulty `stmt` or `setup` in
        # the parent process rather than the valgrind subprocess.
        self._timeit(1)
        is_python = (self._language == Language.PYTHON)
        if not is_python and self._globals:
            raise AssertionError("_timer globals are only supported for Python timers")
        result = valgrind_timer_interface.wrapper_singleton().collect_callgrind(
            task_spec=self._task_spec,
            globals=self._globals,
            number=number,
            repeats=repeats or 1,
            collect_baseline=collect_baseline and is_python,
            is_python=is_python,
            retain_out_file=retain_out_file,
        )

        return (result[0] if repeats is None else result)