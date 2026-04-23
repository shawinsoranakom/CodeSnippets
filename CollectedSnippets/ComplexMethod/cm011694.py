def _is_full_access(cls, buf: str, node: BaseSchedulerNode) -> bool:
        """
        The access to 'buf' is not a broadcast access.
        """
        found_dep = None
        for dep in node.read_writes.reads:
            if isinstance(dep, MemoryDep) and dep.name == buf:
                found_dep = dep
                break

        if not found_dep:
            return False

        index = found_dep.index
        var_ranges = node.read_writes.var_ranges

        if not var_ranges:
            assert isinstance(node, FusedSchedulerNode), f"{type(node)}"
            var_ranges = node.snodes[0].read_writes.var_ranges

        assert var_ranges
        if not (OrderedSet(var_ranges) - OrderedSet(index.free_symbols)):
            return True

        # cases that happen after merging loops:
        #   MemoryDep('arg0_1', c0, {c0: 25165824})])
        #   var_ranges={d0: 32768, d1: 768}
        if V.graph.sizevars.statically_known_equals(
            sympy_product(found_dep.size), sympy_product(var_ranges.values())
        ):
            return True
        return False