def __init__(
        self,
        stmt: str = "pass",
        setup: str = "pass",
        global_setup: str = "",
        timer: Callable[[], float] = timer,
        globals: dict[str, Any] | None = None,
        label: str | None = None,
        sub_label: str | None = None,
        description: str | None = None,
        env: str | None = None,
        num_threads: int = 1,
        language: Language | str = Language.PYTHON,
    ) -> None:
        if not isinstance(stmt, str):
            raise ValueError("Currently only a `str` stmt is supported.")

        # We copy `globals` to prevent mutations from leaking.
        # (For instance, `eval` adds the `__builtins__` key)
        self._globals = dict(globals or {})

        timer_kwargs = {}
        if language in (Language.PYTHON, "py", "python"):
            # Include `torch` if not specified as a convenience feature.
            self._globals.setdefault("torch", torch)
            self._language: Language = Language.PYTHON
            if global_setup:
                raise ValueError(
                    f"global_setup is C++ only, got `{global_setup}`. Most "
                    "likely this code can simply be moved to `setup`."
                )

        elif language in (Language.CPP, "cpp", "c++"):
            if self._timer_cls is not timeit.Timer:
                raise AssertionError("_timer_cls has already been swapped.")
            self._timer_cls = CPPTimer
            setup = ("" if setup == "pass" else setup)
            self._language = Language.CPP
            timer_kwargs["global_setup"] = global_setup

        else:
            raise ValueError(f"Invalid language `{language}`.")

        # Convenience adjustment so that multi-line code snippets defined in
        # functions do not IndentationError (Python) or look odd (C++). The
        # leading newline removal is for the initial newline that appears when
        # defining block strings. For instance:
        #   textwrap.dedent("""
        #     print("This is a stmt")
        #   """)
        # produces '\nprint("This is a stmt")\n'.
        #
        # Stripping this down to 'print("This is a stmt")' doesn't change
        # what gets executed, but it makes __repr__'s nicer.
        stmt = textwrap.dedent(stmt)
        stmt = (stmt[1:] if stmt and stmt[0] == "\n" else stmt).rstrip()
        setup = textwrap.dedent(setup)
        setup = (setup[1:] if setup and setup[0] == "\n" else setup).rstrip()


        self._timer = self._timer_cls(
            stmt=stmt,
            setup=setup,
            timer=timer,
            globals=valgrind_timer_interface.CopyIfCallgrind.unwrap_all(self._globals),
            **timer_kwargs,
        )
        self._task_spec = common.TaskSpec(
            stmt=stmt,
            setup=setup,
            global_setup=global_setup,
            label=label,
            sub_label=sub_label,
            description=description,
            env=env,
            num_threads=num_threads,
        )