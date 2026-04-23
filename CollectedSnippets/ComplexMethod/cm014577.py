def parse(ann: str) -> Annotation:
        # TODO: implement a proper parser if this gets more ugly
        # Regex Explanation:
        # Example: "a! -> a|b"
        # Group #1: alias before optional '|', required. Matches the first
        #   character 'a' in the example
        # Group #2: optional alias set after optional '|', matches empty string
        #   in the example
        # Group #3: optional "is write" flag, matches '!' in the example.
        # Group #4: optional section containing arrow, matches " -> a|b" in the
        #   example.
        # Group #5: optional alias after set, supports wildcard, matches "a|b"
        #   in the example.
        # Group #6: optional sub-section of alias after set, matches "|b" in the
        #   example.
        m = re.match(r"^([a-z])(\|[a-z])*(!?)( -> (\*|[a-z](\|[a-z])*))?$", ann)

        if m is None:
            raise AssertionError(f"unrecognized alias annotation {ann}")
        before_alias = m.group(1) + (m.group(2) if m.group(2) else "")
        alias_set = tuple(before_alias.split("|"))
        is_write = m.group(3) == "!"
        if is_write and len(alias_set) > 1:
            raise AssertionError(
                f"alias set larger than 1 is not mutable, got {ann} instead."
            )
        after_set = tuple(m.group(5).split("|")) if m.group(5) else ()
        if len(before_alias) > 1 and len(after_set) > 1:
            raise AssertionError(
                f"before alias set and after alias set cannot be larger than 1 at the same time, got {ann} instead."
            )
        r = Annotation(
            alias_set=alias_set, is_write=is_write, alias_set_after=after_set
        )
        if str(r) != ann:
            raise AssertionError(f"{r} != {ann}")
        return r