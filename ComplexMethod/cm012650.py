def vars_and_sizes(
        self, index: sympy.Expr
    ) -> tuple[list[sympy.Symbol], list[sympy.Expr]]:
        """Figure out vars from this tree used in index"""

        def get_sort_key(x: IterationRangesEntry) -> tuple[int, bool]:
            """
            Gets the key for sorting nodes. When two nodes have the
            same divisor, the node with length as 1 should be handled
            first so the current divisor is not changed after multiplied
            node.length. Returns `not length_is_one_hint` for ascending
            sort.
            """
            divisor_hint = V.graph.sizevars.optimization_hint(x.divisor)
            length_is_one_hint = V.graph.sizevars.optimization_hint(x.length) == 1
            return (divisor_hint, not length_is_one_hint)

        nodes = [V.kernel.range_tree_nodes.get(s) for s in index.free_symbols]
        nodes = [n for n in nodes if n and n.prefix == self.prefix]
        nodes.sort(key=lambda x: get_sort_key(x))
        divisor = sympy.S.One
        index_vars = []
        sizes = []

        def add(node):
            nonlocal divisor
            index_vars.append(node.symbol())
            sizes.append(node.length)
            divisor = divisor * node.length

        for node in nodes:
            if not V.graph.sizevars.statically_known_equals(node.divisor, divisor):
                # fill in unused index var
                add(self.lookup(divisor, FloorDiv(node.divisor, divisor)))
                divisor = node.divisor
            add(node)
        if not V.graph.sizevars.statically_known_equals(self.numel, divisor):
            # fill in unused index var
            add(self.lookup(divisor, FloorDiv(self.numel, divisor)))

        return [*reversed(index_vars)], [*reversed(sizes)]