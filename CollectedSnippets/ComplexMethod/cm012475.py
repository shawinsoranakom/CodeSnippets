def codegen_input_symbol_assignment(
        self,
        name: str,
        value: ir.TensorBox,
        bound_vars: OrderedSet[sympy.Symbol],
    ):
        code = self.prefix

        @functools.cache
        def sizeof(name):
            code.writeline(f"{name}_size = {name}.size()")
            return f"{name}_size"

        @functools.cache
        def strideof(name):
            code.writeline(f"{name}_stride = {name}.stride()")
            return f"{name}_stride"

        if isinstance(value, sympy.Expr):
            if not isinstance(value, sympy.Symbol) or value in bound_vars:
                return
            code.writeline(f"{value} = {name}")
            bound_vars.add(value)
        elif isinstance(value, ir.TensorBox):
            for dim, size in enumerate(value.get_size()):
                if isinstance(size, sympy.Symbol) and size not in bound_vars:
                    code.writeline(f"{size} = {sizeof(name)}[{dim}]")
                    bound_vars.add(size)
            for dim, stride in enumerate(value.get_stride()):
                if isinstance(stride, sympy.Symbol) and stride not in bound_vars:
                    code.writeline(f"{stride} = {strideof(name)}[{dim}]")
                    bound_vars.add(stride)
        elif isinstance(
            value, (ir.TorchBindObject, ir.GeneratorState, ir.OpaqueObjectState)
        ):
            return
        else:
            if torch._inductor.config.graph_partition:
                pass
            else:
                raise AssertionError(f"Unknown value type: {type(value)}")