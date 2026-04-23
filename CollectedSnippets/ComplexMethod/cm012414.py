def _codegen_v2_raw_input_symbols(self, code: IndentedBuffer) -> None:
        bound_vars = OrderedSet[sympy.Symbol]()
        graph_inputs = self.get_graph_inputs()
        inputs = [
            (k, v) for k, v in graph_inputs.items() if isinstance(v, sympy.Symbol)
        ] + [(k, v) for k, v in graph_inputs.items() if not isinstance(v, sympy.Symbol)]

        # Temporarily redirect self.prefix so the base class
        # codegen_input_symbol_assignment writes into our buffer.
        orig_prefix = self.prefix
        self.prefix = code
        try:
            for name, value in inputs:
                self.codegen_input_symbol_assignment(name, value, bound_vars)
        finally:
            self.prefix = orig_prefix

        for _, value in inputs:
            if not isinstance(value, ir.TensorBox):
                continue
            for expr in [*value.get_size(), *value.get_stride()]:
                if not isinstance(expr, sympy.Expr) or isinstance(expr, sympy.Symbol):
                    continue
                undefined_symbols = [
                    sym for sym in expr.free_symbols if sym not in bound_vars
                ]
                if len(undefined_symbols) > 0:
                    raise AssertionError(
                        f"For {expr}, expected {undefined_symbols} to have been codegen-ed."
                    )