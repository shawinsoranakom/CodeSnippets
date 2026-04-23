def check_prologue_fusion_heuristics_fusable(
        self,
        prologue_node: BaseSchedulerNode,
        template_node: BaseSchedulerNode,
        why: WhyNoFuse,
    ) -> bool:
        """
        Heuristics to avoid benchmarking predictably slow prologue fusions
        """
        # user opt into more aggressive prologue fusion, dont use heuristics
        if prologue_node.get_operation_names() <= V.graph.invoke_quant_ops:
            return True

        read_bytes = prologue_node.get_read_buffer_sizes()
        write_bytes = prologue_node.get_write_buffer_sizes()

        # Initially, only do fusions which will result in fewer memory accesses inside of the template to avoid
        # potential bad cache behavior and shared memory use.
        # we also want to avoid benchmarking reliably unprofitable fusions like downcasts from fp32 -> fp16 inside kernel.
        # allowing gathers by allowing increasing write_bytes by small factor
        # TODO - make configurable per input, for instance, bias can fuse fp32 -> fp16 profitably

        BYTES_THRESHOLD_MULTIPLIER = 1.1
        if read_bytes > (write_bytes * BYTES_THRESHOLD_MULTIPLIER):
            why("prologue fusion will not increase amount of bytes read in kernel")
            return False

        # we want to avoid attempting to fuse predictably unprofitable prologues
        # such as increasing the unaligned reads or writes.
        # TODO - would be nice to generalize this, however, we would need more explicit
        # knowledge of memory access patterns in the TritonTemplate in order to know
        # the stride order to check alignment.
        origins = tuple(
            e.target
            for n in prologue_node.get_nodes()
            if n.node is not None
            for e in n.node.get_origins()
            if e.op == "call_function"
        )
        if origins == (torch.ops.aten.constant_pad_nd.default,):
            why(
                "prologue fusion will not increase attempt to fuse in padding bc it increases unaligned reads"
            )
            return False

        def low_prec_fp(dtype: torch.dtype) -> bool:
            return dtype.itemsize <= 2 and dtype.is_floating_point

        template_buf = template_node.get_template_node_or_throw()
        if (
            not template_buf.is_multi_outputs_template()
            and low_prec_fp(template_buf.dtype)
            and not prologue_node.can_codegen_in_low_precision()
        ):
            why(
                "prologue fusion that must be upcast to fp32 not profitable for low precision templates"
            )
            return False

        return True