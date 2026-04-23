def _generate_scatter_fallback(self, line: WrapperLine) -> None:
        assert isinstance(line, ScatterFallbackLine)
        ir_node = line.node
        assert ir.is_node_sequence(ir_node.inputs)
        (x, index, src) = [self._generate_buffer(t) for t in ir_node.inputs] + (
            [] if ir_node.src_is_tensor else [ir_node.constant_args[1]]
        )
        args = (x, ir_node.constant_args[0], index, src)
        kwargs = {}
        if reduce := ir_node.kwargs.get("reduce"):
            kwargs["reduce"] = reduce
        # Only pass kwargs that the op's schema actually accepts, since
        # ScatterFallback stores both reduce and include_self for all
        # scatter variants, but not all ops support them (e.g.,
        # scatter_.value has no kwargs, scatter_reduce_.two has both).
        assert isinstance(ir_node.op_overload, torch._ops.OpOverload)
        schema_arg_names = OrderedSet(
            [a.name for a in ir_node.op_overload._schema.arguments]
        )
        kwargs = {k: v for k, v in ir_node.kwargs.items() if k in schema_arg_names}

        self._generate_fallback_call(ir_node, args, kwargs)