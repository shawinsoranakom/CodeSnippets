def finalize_indexing(self, indices: Sequence[sympy.Expr]):
        """
        Hook called right before codegen with every index that will be
        used in the fused kernel.

        This populates self.halide_vars/index_replacements/reduction_renames which is an alternate indexing
        scheme that avoids using divide and modulus.  Instead of xindex/yindex/rindex
        we base indexing on a larger number of vars whose product combines to those.

        This function populates self.halide_vars, self.index_replacements, and self.reduction_renames
        """
        assert not (
            self.index_replacements or self.halide_vars or self.reduction_renames
        )
        size_hint = functools.partial(
            V.graph.sizevars.optimization_hint, fallback=sys.maxsize
        )
        # pyrefly: ignore [bad-assignment]
        indices = dict.fromkeys(map(super().prepare_indexing, indices))
        all_used_symbols = OrderedSet[Any]()
        sym_to_node = {
            n.symbol(): n
            for n in itertools.chain.from_iterable(
                [tree.nodes.values() for tree in self.range_trees]
            )
        }

        def simplify(expr):
            return sympy.simplify(
                V.graph.sizevars.remove_precomputed_replacements(expr)
            )

        def visit_modular_indexing(base, divisor, modulus):
            if base in sym_to_node:
                node = sym_to_node[base]
                all_used_symbols.add(
                    node.root.lookup(
                        node.divisor * divisor,
                        V.graph.sizevars.evaluate_min(
                            modulus,
                            FloorDiv(node.length, divisor),
                        ),
                    ).symbol()
                )

        def visit_floor_div(base, divisor):
            if base in sym_to_node:
                node = sym_to_node[base]
                all_used_symbols.add(
                    node.root.lookup(
                        node.divisor * divisor,
                        FloorDiv(node.length, divisor),
                    ).symbol()
                )

        # first figure out all_used_symbols to do dead symbol elimination
        for index in indices:
            if index.has(ModularIndexing):
                index.replace(
                    ModularIndexing(
                        sympy.Wild("base"),
                        sympy.Wild("divisor"),
                        sympy.Wild("modulus"),
                    ),
                    visit_modular_indexing,
                )
            if index.has(FloorDiv):
                index.replace(
                    FloorDiv(
                        sympy.Wild("base"),
                        sympy.Wild("divisor"),
                    ),
                    visit_floor_div,
                )
            all_used_symbols.update(super().prepare_indexing(index).free_symbols)

        self.has_indirect_indexing = any(
            symbol_is_type(sym, SymT.INDIRECT) for sym in all_used_symbols
        )

        had_fallback = False
        for tree in reversed(self.range_trees):
            nodes = [n for n in tree.nodes.values() if n.symbol() in all_used_symbols]
            nodes.sort(key=lambda n: size_hint(n.divisor))
            if not nodes:
                nodes.append(tree.lookup(1, tree.numel))
            handled_count = 0
            divisor = sympy.S.One
            added_sym_size = []
            # decide on a minimal set of symbols and put them in self.halide_vars
            while handled_count < len(nodes) and not eq(tree.numel, divisor):
                sizes_to_add = [
                    simplify(n.length) for n in nodes if eq(n.divisor, divisor)
                ]
                handled_count += len(sizes_to_add)
                assert sizes_to_add, nodes
                end = divisor * functools.reduce(
                    lambda a, b: V.graph.sizevars.evaluate_max(a, b),
                    sizes_to_add,
                )
                sizes_to_add.extend(
                    [
                        simplify(n.divisor / divisor)
                        for n in nodes
                        if lt(divisor, n.divisor) and lt(n.divisor, end)
                    ]
                )
                # pyrefly: ignore [bad-assignment]
                while sizes_to_add:
                    next_size = functools.reduce(sympy.gcd, sizes_to_add)
                    if eq(next_size, 1):
                        # sizes share no common factors, e.g [2, 21, 42, 441, 889056]
                        # TODO(jansel): we should just prevent fusion in cases that hit this
                        next_size = simplify(tree.numel / divisor)
                        assert not eq(next_size, 1)
                        sizes_to_add = []
                        handled_count = len(nodes)
                        had_fallback = True
                    sym = sympy_index_symbol(f"h{len(self.halide_vars)}")
                    # pyrefly: ignore [missing-argument]
                    if tree.is_reduction:
                        self.reduction_renames[sym] = sympy_index_symbol(
                            f"hr{len(self.halide_vars)}"
                        )
                    self.halide_vars[sym] = next_size
                    added_sym_size.append((sym, next_size))
                    divisor *= next_size
                    new_sizes = [n.length for n in nodes if eq(n.divisor, divisor)]
                    handled_count += len(new_sizes)
                    prior_len = len(sizes_to_add)
                    sizes_to_add = [
                        sympy.simplify(s / next_size)
                        for s in sizes_to_add
                        if not eq(s, next_size)
                    ]
                    assert len(sizes_to_add) < prior_len or prior_len == 0
                    sizes_to_add.extend(new_sizes)

            # create a mapping to the new set of symbols in self.index_replacements
            for node in nodes:
                try:
                    idx = 0
                    divisor = 1
                    while not eq(node.divisor, divisor):
                        sym, size = added_sym_size[idx]
                        idx += 1
                        divisor *= size
                    length = 1
                    expr = sympy.S.Zero
                    while not eq(node.length, length):
                        sym, size = added_sym_size[idx]
                        idx += 1
                        expr += length * sym
                        length *= size
                    self.index_replacements[node.symbol()] = expr
                except IndexError:
                    assert had_fallback
                    full_index = sympy.S.Zero
                    stride = sympy.S.One
                    for sym, size in added_sym_size:
                        full_index += stride * sym
                        stride *= size
                    self.index_replacements[node.symbol()] = (
                        V.graph.sizevars.simplify_with_ranges(
                            ModularIndexing(full_index, node.divisor, node.length),
                            self.halide_vars,  # type: ignore[arg-type]
                        )
                    )

        # codegen the variable definitions
        for sym in self.halide_vars:
            self.indexing_code.writeline(f"{sym} = hl.Var({sym.name!r})")
        if self.reduction_renames:
            self.codegen_rdom(
                "rdom",
                {rv: self.halide_vars[v] for v, rv in self.reduction_renames.items()},
            )