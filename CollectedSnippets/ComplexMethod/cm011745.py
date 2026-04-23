def should_partition(self, node: BaseSchedulerNode) -> str | None:
        """
        Return the reason why we should partition the inductor graph on this node,
        or None if the node is cudagraphable.
        """

        # Allow users to manually specify if a node should be partitioned
        # Can only do this for FallbackKernels
        ir_node = node.node
        if isinstance(ir_node, torch._inductor.ir.FallbackKernel) and (
            op := ir_node.op_overload
        ):
            op_overload_packet_name, op_overload_name = get_op_names(op)
            if (
                op_overload_packet_name in config.custom_should_partition_ops
                or op_overload_name in config.custom_should_partition_ops
            ):
                assert isinstance(op, torch._ops.OpOverload)
                return f"custom partition op: {op_overload_name}"

        # When not using cudagraphs, keep all kernels in the `call` function
        # instead of graph partition functions, since graph partition only brings
        # benefit to cudagraph
        if (
            not torch._inductor.config.triton.cudagraphs
            and _unstable_customized_partition_wrapper.wrapper is None
        ):
            return "partition includes all ops when cudagraphs is disabled"

        if isinstance(node, FusedSchedulerNode):
            for snode in node.snodes:
                reason = self.should_partition(snode)
                if reason:
                    return reason
            return None

        assert node.node is not None

        if not node.is_gpu():
            return f"{node.get_device()} ops"

        if isinstance(node.node, ir.DeviceCopy):
            return "DeviceCopy ops"

        if isinstance(node.node, ir.Conditional):
            return "Conditional ops"

        if getattr(node.node, "unbacked_bindings", None):
            return "unbacked binding ops"

        if is_cudagraph_unsafe_op(node.node):
            return "CUDAGraph-unsafe custom ops"

        if reason := self._uses_cudagraph_unsafe_unbacked_symint(node):
            return reason

        # Partition around nodes with dynamic shapes when cudagraph_skip_dynamic_graphs is enabled
        if config.triton.cudagraph_skip_dynamic_graphs:
            if get_scheduler_node_symbol_uses(node):
                return "dynamic shape ops"

        return None