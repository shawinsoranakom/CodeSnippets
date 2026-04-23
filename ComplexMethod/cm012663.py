def _codegen_single_template(
        self,
        kernel,
        render,
        template_node,
        epilogue_nodes,
        prologue_nodes,
        *,
        only_gen_src_code=False,
    ):
        """
        Helper method to codegen a single template kernel variant
        """
        buf_name_to_prologue_group = {}
        template_reads = template_node.used_buffer_names()
        prologue_group = []
        for prologue in prologue_nodes:
            names = prologue.get_buffer_names()
            prologue_group.append(prologue)
            # this must be the end of a prologue group
            if names & template_reads:
                assert len(names) == 1
                buf_name_to_prologue_group[next(iter(names))] = prologue_group
                kernel.prologue_fused_inputs.add(next(iter(names)))
                prologue_group = []

        # all prologue groups should have finalized with use in template
        assert len(prologue_group) == 0

        # Remove prologue-fused inputs from input_buffers so that
        # remove_kernel_local_buffers can remove them.
        for buf_name in kernel.prologue_fused_inputs:
            kernel.args.input_buffers.pop(buf_name, None)

        # Dispatch to the kernel for source generation.  TritonTemplateKernel
        # handles the standard Triton path; ExternalTritonTemplateKernel
        # handles external backends (e.g. Helion).
        src_code = kernel.codegen_template_body(
            self,
            template_node,
            epilogue_nodes,
            prologue_nodes,
            buf_name_to_prologue_group,
            prologue_preserves_zero_mask,
            render,
        )

        if config.benchmark_kernel:
            num_gb = kernel.estimate_kernel_num_bytes() / 1e9
            src_code = (
                f"{kernel.imports_for_benchmark_kernel()}\n"
                f"{src_code}\n"
                f"{kernel.codegen_kernel_benchmark(num_gb).getvalue()}"
            )

        node_schedule = [*prologue_nodes, template_node, *epilogue_nodes]

        if only_gen_src_code:
            return src_code

        # Unfused epilogues are codegen'd separately in call_kernel;
        # exclude them from mark_run.
        unfused_set = OrderedSet([id(n) for n in kernel.get_unfused_epilogues()])
        with V.set_kernel_handler(kernel):
            template_node.mark_run()
            for node in epilogue_nodes:
                if id(node) not in unfused_set:
                    node.mark_run()
            for node in prologue_nodes:
                node.mark_run()

        kernel.kernel_name = self.define_kernel(src_code, node_schedule, kernel)

        return kernel