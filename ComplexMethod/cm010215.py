def _process_sym_expr(
            sym: sympy.Expr, hint: int | bool | float | None = None
        ) -> sympy.Expr:
            if sym.is_Integer or sym.is_Float or sym.is_Boolean:  # base case
                return sym
            else:  # recursive case
                # important to use str(expr) and not _print_sympy(),
                # str(expr) is key for self.symbol_name_to_range
                expr_str = str(sym)
                for arg in sym.args:
                    self._parse_sym_expr(arg)
                # symbol caching
                if expr_str in self.symbol_name_to_symbol:
                    sym = self.symbol_name_to_symbol[expr_str]
                else:
                    self.symbol_name_to_symbol[expr_str] = sym
                    if isinstance(sym, sympy.Symbol) and symbolic_shapes.symbol_is_type(
                        sym, (SymT.UNBACKED_INT, SymT.UNBACKED_FLOAT)
                    ):
                        self.unbacked_symbols.add(sym)
                # hints
                if hint is not None and sym not in self.shape_env.backed_var_to_val:
                    self.shape_env.add_backed_var_to_val(sym, hint)  # type: ignore[arg-type]
                # ValueRanges
                if vr := self.symbol_name_to_range.get(expr_str):
                    self.shape_env.constrain_symbol_range(
                        sym,
                        compiler_min=vr.lower,  # type: ignore[arg-type]
                        compiler_max=vr.upper,  # type: ignore[arg-type]
                    )
                # ShapeEnv meta
                if isinstance(sym, sympy.Symbol):
                    self.shape_env.var_to_stack[sym] = CapturedTraceback.extract(skip=1)
            return sym