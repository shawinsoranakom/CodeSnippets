def _get_cudagraph_unsafe_unbacked_symints(self) -> OrderedSet[sympy.Symbol]:
        """
        Collect output unbacked symints from ops in config.cudagraph_unsafe_unbacked_ops.
        """
        unsafe_symints: OrderedSet[sympy.Symbol] = OrderedSet()

        if not config.cudagraph_unsafe_unbacked_ops:
            return unsafe_symints

        for node in self.nodes:
            ir_node = node.node
            if ir_node is None:
                continue

            if not isinstance(ir_node, torch._inductor.ir.FallbackKernel):
                continue

            op = ir_node.op_overload
            if op is None:
                continue

            op_overload_packet_name, op_overload_name = get_op_names(op)
            if (
                op_overload_packet_name not in config.cudagraph_unsafe_unbacked_ops
                and op_overload_name not in config.cudagraph_unsafe_unbacked_ops
            ):
                continue

            for sym in ir_node.get_unbacked_symbol_defs():
                sym = V.graph.sizevars.simplify(sym)
                if symbol_is_type(sym, (SymT.UNBACKED_INT, SymT.UNBACKED_FLOAT)):
                    unsafe_symints.add(sym)

        return unsafe_symints