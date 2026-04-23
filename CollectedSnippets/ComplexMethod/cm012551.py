def indexing_to_dimensions(self, var: str, index: sympy.Expr, is_store: bool):
        """Convert address-based indexing into dimensions using self.halide_vars"""
        symbols = []
        for sym in sorted(index.free_symbols, key=lambda x: x.name):  # type: ignore[attr-defined]
            if symbol_is_type(sym, (SymT.HALIDE, SymT.TMP)):
                symbols.append(sym)
            else:
                assert symbol_is_type(
                    sym,
                    (
                        SymT.UNBACKED_INT,
                        SymT.SIZE,
                        SymT.PRECOMPUTED_SIZE,
                    ),
                ), sym

        # group the expression by variables used
        offset = sympy.S.Zero
        split_expr = dict.fromkeys(symbols, sympy.S.Zero)
        split_failed: list[tuple[list[sympy.Symbol], sympy.Expr]] = []
        index = sympy.expand(self.rename_indexing(index))
        for part in index.args if isinstance(index, sympy.Add) else [index]:
            part_vars = [v for v in part.free_symbols if v in split_expr]
            if len(part_vars) == 0:
                offset += part
            elif len(part_vars) == 1:
                split_expr[part_vars[0]] += part
            else:
                new_split_failed = []
                for i in range(len(split_failed)):
                    assert split_failed[i] is not None
                    other_vars, other_part = split_failed[i]
                    if OrderedSet(other_vars) & OrderedSet(part_vars):
                        part_vars.extend([v for v in other_vars if v not in part_vars])
                        part += other_part
                    else:
                        new_split_failed.append((other_vars, other_part))
                split_failed = [*new_split_failed, (part_vars, part)]

        def expr_to_dimension(expr, syms):
            expr = sympy.factor(expr)
            if len(syms) == 1:
                stride_wild = sympy.Wild("wild", exclude=symbols)
                m = expr.match(stride_wild * syms[0])
                if m:
                    return DimensionInfo(
                        syms[0], self.sym_size(syms[0]), m[stride_wild]
                    )
            assert not is_store, expr
            length = sympy.simplify(
                sympy_subs(expr, {sym: self.sym_size(sym) - 1 for sym in syms}) + 1
            )
            stride = sympy.S.One
            if isinstance(expr, sympy.Mul):
                for term in expr.args:
                    if isinstance(term, sympy.Integer):
                        stride *= term
                        expr = sympy.simplify(expr / term)
                        length = sympy.simplify(sympy.ceiling(length / term))
            return DimensionInfo(expr, length, stride)

        # try to turn each group into a strided access
        dims = []
        for syms, expr in split_failed:
            for v in syms:
                expr += split_expr.pop(v)
            dims.append(expr_to_dimension(expr, syms))
        for sym, expr in split_expr.items():
            dims.append(expr_to_dimension(expr, [sym]))
        dims.sort(
            key=lambda d: V.graph.sizevars.optimization_hint(
                d.stride, fallback=sys.maxsize
            )
        )  # type: ignore[arg-type]

        if not dims:  # scalar load/store
            if self.has_indirect_indexing:
                # workaround https://github.com/halide/Halide/issues/8338
                dims.append(DimensionInfo(sympy.S.Zero, 1, 1))
        elif not V.graph.sizevars.statically_known_equals(dims[0].stride, 1):
            # Halide assumes dimension 0 is stride == 1, so add a dummy dimension
            dims.insert(
                0, DimensionInfo(sympy.S.Zero, 1 if is_store else dims[0].stride, 1)
            )

        if dims and not is_store:
            if var in self.buffer_offsets and V.graph.sizevars.statically_known_geq(
                offset, self.buffer_offsets[var]
            ):
                # reuse the existing offset to avoid needing an input alias
                self.apply_offset_to_dimension(dims, offset - self.buffer_offsets[var])
                offset = self.buffer_offsets[var]
            elif V.graph.sizevars.statically_known_gt(
                offset, 0
            ):  # TODO(jansel): negative offsets
                # roll the offset into the dimensions for cleaner indexing
                self.apply_offset_to_dimension(dims, offset)
                offset = 0

        orig_var = var
        for i in itertools.count():
            if self.install_dims(var, dims, offset, is_store):
                return var, dims
            assert not is_store
            var = f"{orig_var}_view{i}"
            if var not in self.buffer_aliases[orig_var]:
                self.buffer_aliases[orig_var].append(var)