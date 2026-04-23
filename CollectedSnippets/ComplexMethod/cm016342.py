def __init__(
        self,
        name: str,
        excluded: Iterable[str] | None = None,
        included: Iterable[str] | None = None,
    ) -> None:
        if excluded and included:
            raise ValueError("Can't specify both included and excluded")

        ins = set(included or [])
        exs = set(excluded or [])

        if "::" in name:
            if included or excluded:
                raise AssertionError(
                    "Can't specify included or excluded tests when specifying a test class in the file name"
                )
            self.test_file, test_class = name.split("::")
            ins.add(test_class)
        else:
            self.test_file = name

        self._excluded = frozenset(exs)
        self._included = frozenset(ins)