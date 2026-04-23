def _can_fuse_epilogue_impl(
        self,
        cutlass_template_buffer: CUTLASSTemplateBuffer,
        existing_epilogue_nodes: list[BaseSchedulerNode],
        node_to_fuse: BaseSchedulerNode,
    ) -> bool:
        """
        Check if the given node can be fused with the epilogue. At the moment, Kernels
        support fusion with Pointwise operations, wrapped in (named) ComputedBuffer nodes.

        Args:
            cutlass_template_buffer : A CUTLASSTemplateBuffer object representing the CUTLASS template and it's result buffer
            existing_epilogue_nodes : List[SchedulerNode]: The list of already fused epilogue nodes.
            node_to_fuse: The SchedulerNode node to be checked if it can be fused with the epilogue.
        Returns:
        - bool: True if the given node can be fused with the epilogue, False otherwise.

        """
        why = WhyNoFuseNames(
            cutlass_template_buffer.get_name(), node_to_fuse.get_name()
        )

        scheduler_nodes_to_fuse = node_to_fuse.get_nodes()

        assert isinstance(cutlass_template_buffer, CUTLASSTemplateBuffer)

        # Checks on constituent nodes
        for s_node in scheduler_nodes_to_fuse:
            node = s_node.node

            if not isinstance(node, ComputedBuffer):
                why(f"{node} is not a ComputedBuffer")
                return False
            elif not isinstance(node.data, Pointwise):
                why(f"{node} is not a Pointwise op")
                return False
            elif not node.get_computed_buffer_name():  # type: ignore[attr-defined]
                why(f"{node} does not have a computed buffer name")
                return False

            name = node.get_computed_buffer_name()  # type: ignore[attr-defined]
            # dtype can differ, and strides can differ as long as they are broadcastable
            if node.get_size() != cutlass_template_buffer.get_size():
                why(
                    f"{name}'s size: {node.get_size()} differs from {cutlass_template_buffer.get_name()}'s \
size: {cutlass_template_buffer.get_size()}"
                )
                return False

        assert len(
            existing_epilogue_nodes
        ) or cutlass_template_buffer.get_name() in OrderedSet(
            [rd.name for rd in node_to_fuse.read_writes.reads]
        ), "First epilogue node must read from cutlass template buffer"

        if node_to_fuse.has_aliasing_or_mutation():
            why(f"{node_to_fuse.get_name()} has aliasing or mutation")
            return False
        elif node_to_fuse.is_reduction():
            why(
                f"{node_to_fuse.get_name()} is a reduction which is not yet supported by EVT"
            )
            return False
        elif (
            not config.cutlass.cutlass_epilogue_fusion_enabled
            or not config.epilogue_fusion
        ):
            why("cutlass epilogue fusion is not enabled")
            return False
        elif not cutlass_template_buffer.supports_epilogue_fusion:
            why("epilogue fusion is only supported for TMA-enabled gemm ops")
            return False

        try:
            from torch._inductor.codegen.cutlass.python_evt import CutlassEVTCodegen

            CutlassEVTCodegen.ir_to_evt_python_code(
                cutlass_template_buffer.get_name(),
                existing_epilogue_nodes + list(node_to_fuse.get_nodes()),
                OrderedSet(),
            )

        except NotImplementedError as e:
            not_implemented_op = str(e)
            if not_implemented_op.startswith("_op_"):
                not_implemented_op = not_implemented_op[4:]
                why(
                    f"Cannot fuse epilogue node {node_to_fuse} into {cutlass_template_buffer.name}, \
likely due to unsupported operation: {not_implemented_op}"
                )
                return False
            else:  # Likely due to unsupported dtype.
                why(
                    f"Cannot fuse epilogue node {node_to_fuse} into {cutlass_template_buffer.name}. \
Reason: {not_implemented_op}"
                )
                return False

        return True