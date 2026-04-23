def codegen_template(
        self,
        template_node: BaseSchedulerNode,
        epilogue_nodes: Sequence[BaseSchedulerNode],
        prologue_nodes: Sequence[BaseSchedulerNode],
    ):
        """
        Codegen a cutlass template, possibly with fused epilogues
        """
        counters["inductor"]["cutlass_epilogue_fusion_counter"] += len(epilogue_nodes)
        assert self.is_cutlass_template(template_node), (
            "Template node passed to CUTLASSScheduling.codegen_template must be a SchedulerNode that wraps a CUTLASSTemplateBuffer"
        )
        _, (_numel, rnumel) = template_node.group
        assert rnumel == 1
        ctb: CUTLASSTemplateBuffer = cast(CUTLASSTemplateBuffer, template_node.node)
        epilogue_ir_nodes: list[Buffer] = [n.node for n in epilogue_nodes]  # type: ignore[misc]
        assert all(isinstance(n, ComputedBuffer) for n in epilogue_ir_nodes), (
            "Epilogue nodes must all be instances of ir.ComputedBuffer"
        )
        kernel, render = ctb.make_kernel_render(  # type: ignore[misc]
            ctb, epilogue_nodes=epilogue_nodes
        )
        with kernel:
            for node in [template_node, *epilogue_nodes]:
                node.mark_run()

            # typically there is a codegen pass which runs after mark_run
            # for this kernel we've already generated the C++ code, but we still
            # need to let the kernel know about loads/stores that occur in the fused
            # kernel for memory planning to properly optimize allocations
            ctb.emulate_store_fn()
            for node in epilogue_ir_nodes:
                with V.set_ops_handler(MockCutlassHandler(V.get_ops_handler())):
                    assert isinstance(
                        node, ComputedBuffer
                    )  # Not sure why we need to do this again
                    node.get_store_function()(CutlassEVTCodegen.get_index_vars(node))

        with V.set_kernel_handler(kernel):
            src_code = render()
            node_schedule = [template_node, *epilogue_nodes]
            kernel_name = self.define_kernel(src_code, node_schedule)

        # debug printing values of intermediate tensors
        _, call_args, arg_signatures, _ = kernel.args.python_argdefs()
        debug_printer_manager = V.graph.wrapper_code.debug_printer
        debug_printer_manager.set_printer_args(
            call_args, kernel_name, arg_signatures, kernel
        )
        with debug_printer_manager:
            self.codegen_comment(node_schedule, kernel_name)
            kernel.call_kernel(kernel_name, ctb)

        V.graph.removed_buffers |= kernel.removed_buffers
        self.free_buffers_in_scheduler()