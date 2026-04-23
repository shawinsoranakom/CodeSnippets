def init_from_variants(
        cls,
        py_block: str = "",
        cpp_block: str = "",
        num_threads: int | tuple[int, ...] = 1,
    ) -> dict[tuple[str, ...] | str | None, "GroupedBenchmark"]:
        py_cases, py_setup, py_global_setup = cls._parse_variants(
            py_block, Language.PYTHON
        )
        cpp_cases, cpp_setup, cpp_global_setup = cls._parse_variants(
            cpp_block, Language.CPP
        )

        if py_global_setup:
            raise AssertionError(
                f"py_global_setup should be empty, but got: {py_global_setup}"
            )
        setup = GroupedSetup(
            py_setup=py_setup,
            cpp_setup=cpp_setup,
            global_setup=cpp_global_setup,
        )

        # NB: The key is actually `Tuple[str, ...]`, however MyPy gets confused
        #     and we use the superset `Union[Tuple[str, ...], Optional[str]` to
        #     match the expected signature.
        variants: dict[tuple[str, ...] | str | None, GroupedBenchmark] = {}

        seen_labels: set[str] = set()
        for label in it.chain(py_cases.keys(), cpp_cases.keys()):
            if label in seen_labels:
                continue
            seen_labels.add(label)

            py_lines = py_cases.get(label, [])
            cpp_lines = cpp_cases.get(label, [])

            n_lines = max(len(py_lines), len(cpp_lines))
            py_lines += [""] * (n_lines - len(py_lines))
            cpp_lines += [""] * (n_lines - len(cpp_lines))
            lines = [
                (py_stmt, cpp_stmt)
                for py_stmt, cpp_stmt in zip(py_lines, cpp_lines)
                if py_stmt or cpp_stmt
            ]

            for i, (py_stmt, cpp_stmt) in enumerate(lines):
                case = (f"Case: {i:>2}",) if len(lines) > 1 else ()
                variants[(label,) + case] = GroupedBenchmark.init_from_stmts(
                    py_stmt=py_stmt or None,
                    cpp_stmt=cpp_stmt or None,
                    setup=setup,
                    num_threads=num_threads,
                )

        return variants