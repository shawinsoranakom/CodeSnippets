def _codegen_symbol(
            sym_or_exp: sympy.Symbol | sympy.Expr,
            base_node: torch.fx.Node,
            target: torch._ops.OpOverload,
            dim: int,
        ) -> None:
            def codegen_proxy() -> torch.fx.Proxy:
                size_node = self.gm.graph.call_function(target, (base_node, dim))
                size_proxy = self._generate_size_proxy(size_node, sym_or_exp)
                return size_proxy

            if isinstance(sym_or_exp, sympy.Symbol):
                if sym_or_exp in self.expr_to_proxy:
                    return
                codegen_proxy()

            elif isinstance(sym_or_exp, sympy.Integer):
                return

            elif isinstance(sym_or_exp, sympy.Expr):
                # Check if we need to solve for an undefined symbol.
                undefined_symbols = [
                    sym
                    for sym in sym_or_exp.free_symbols
                    if sym not in self.expr_to_proxy
                ]
                if len(undefined_symbols) == 0:
                    self._sympy_interp(sym_or_exp)
                    return
                elif len(undefined_symbols) > 1:
                    raise ValueError(f"Underdetermined input expression: {sym_or_exp}")

                # Define a new symbol for the input size.
                size_proxy = codegen_proxy()
                size_symbol = sympy.Symbol(
                    size_proxy.node.name, integer=True, nonnegative=True
                )
                self.expr_to_proxy[size_symbol] = size_proxy

                # Solve for the undefined symbol.
                undefined_symbol = undefined_symbols[0]
                solution = try_solve(
                    sympy.Eq(sym_or_exp, size_symbol), undefined_symbol
                )
                if solution is None:
                    raise ValueError(f"Cannot solve input expression: {sym_or_exp}")

                # Since the symbol is a size, it must be an integer.
                # Therefore, we can convert division to FloorDiv.
                undefined_symbol_expr = solution[1]
                if undefined_symbol.is_integer:
                    undefined_symbol_expr = replace_floor_div(
                        sympy.floor(undefined_symbol_expr)
                    )

                # Generate FX for the symbol.
                self._sympy_interp(undefined_symbol_expr)
                self.expr_to_proxy[undefined_symbol] = self.expr_to_proxy[
                    undefined_symbol_expr
                ]