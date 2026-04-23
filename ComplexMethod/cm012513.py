def _eliminate_dead_indirect_code(self) -> None:
        """Remove dead compute lines after scalar prefetch replaces indirect load.

        When the table load is simplified to buf[0] (scalar prefetch handles
        indexing), the indices load and all derived bounds-checking code become
        dead.  This performs backward liveness analysis from the store variables
        to identify and remove dead lines.
        """
        # Collect variables used by stores (live roots)
        live_vars: OrderedSet[str] = OrderedSet()
        for _, store_line in self.store_with_output:
            for m in re.finditer(r"\btmp\d+\b", store_line):
                live_vars.add(m.group())

        # Parse assignments from compute lines
        assignments: list[tuple[str | None, str, Any]] = []
        for line in self.compute._lines:
            line_str = str(line).lstrip()
            m = re.match(r"^(tmp\d+)\s*=\s*(.*)", line_str, re.DOTALL)
            if m:
                assignments.append((m.group(1), m.group(2), line))
            else:
                assignments.append((None, line_str, line))

        # Propagate liveness backward
        changed = True
        while changed:
            changed = False
            for var_name, rhs, _ in reversed(assignments):
                if var_name and var_name in live_vars:
                    for m in re.finditer(r"\btmp\d+\b", rhs):
                        if m.group() not in live_vars:
                            live_vars.add(m.group())
                            changed = True

        # Keep only live assignments (and non-assignment lines)
        self.compute._lines = [
            line
            for var_name, _, line in assignments
            if var_name is None or var_name in live_vars
        ]