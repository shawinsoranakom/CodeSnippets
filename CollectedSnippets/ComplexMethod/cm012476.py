def codegen_inputs(self):
        """Assign all symbolic shapes to locals"""
        bound_vars = OrderedSet[sympy.Symbol]()
        # There is a subtle case in the cpp wrapper codegen which requires generating
        # symbol inputs first followed by non-symbol ones.
        #
        # When a dynamic size constraint specified at the Export time is an expression,
        # we need to solve that expression to proper define a symbol in cpp. Thus we
        # are enforcing this iterating order here to make sure all plain size symbols
        # are defined first.
        graph_inputs = self.get_graph_inputs()
        inputs = [
            (k, v) for k, v in graph_inputs.items() if isinstance(v, sympy.Symbol)
        ] + [(k, v) for k, v in graph_inputs.items() if not isinstance(v, sympy.Symbol)]
        for name, value in inputs:
            self.codegen_input_symbol_assignment(name, value, bound_vars)

        def _verify_input_symbol_assignment(
            value: ir.TensorBox,
            bound_vars: OrderedSet[sympy.Symbol],
        ):
            for expr in chain.from_iterable([value.get_size(), value.get_stride()]):
                if not isinstance(expr, Expr) or isinstance(expr, sympy.Symbol):
                    continue

                undefined_symbols = [
                    sym for sym in expr.free_symbols if sym not in bound_vars
                ]
                if len(undefined_symbols) > 0:
                    raise AssertionError(
                        f"For {expr}, expected {undefined_symbols} to have been codegen-ed."
                    )

        # For inputs with size/strides which contain sympy expressions, we can
        # encounter symbols that weren't defined yet. Now, let's check each
        # symbol is defined.
        for _, value in inputs:
            if not isinstance(value, ir.TensorBox):
                continue
            _verify_input_symbol_assignment(value, bound_vars)