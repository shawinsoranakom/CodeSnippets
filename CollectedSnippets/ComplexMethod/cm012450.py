def codegen_template(
        self,
        template_node: BaseSchedulerNode,
        epilogue_nodes: Sequence[BaseSchedulerNode],
        prologue_nodes: Sequence[BaseSchedulerNode],
    ):
        """
        Codegen a CPP template, possibly with fused epilogues
        """
        assert not prologue_nodes

        # remove MultiOutput from epilogue_nodes
        epilogue_nodes = [
            epilogue_node
            for epilogue_node in epilogue_nodes
            if isinstance(epilogue_node, (SchedulerNode, FusedSchedulerNode))
        ]
        # The counter cpp_templated_kernel_counter is used for verifying if a
        # a templated kernel was successfully compiled in a UT
        counters["inductor"]["cpp_templated_kernel_counter"] += 1
        counters["inductor"]["cpp_epilogue_fusion_counter"] += len(epilogue_nodes)
        assert self.is_cpp_template(template_node), (
            "Template node passed to CppScheduler.codegen_template must be a SchedulerNode that wraps a CppTemplateBuffer"
        )
        template_node = cast(SchedulerNode, template_node)
        _, (_, rnumel) = template_node.group
        assert rnumel == ()
        ctb: ir.CppTemplateBuffer = cast(ir.CppTemplateBuffer, template_node.node)
        epilogue_ir_nodes: list[ir.Operation | None] = [n.node for n in epilogue_nodes]
        assert all(isinstance(n, ir.ComputedBuffer) for n in epilogue_ir_nodes), (
            "Epilogue nodes must all be instances of ir.ComputedBuffer"
        )

        def template_buffer_has_other_users(
            template_buffer, outputs_by_name, epilogue_nodes
        ):
            if not epilogue_nodes:
                return False

            assert template_buffer.get_name() in outputs_by_name
            users = outputs_by_name[template_buffer.get_name()].users
            return not all(
                isinstance(user.node, BaseSchedulerNode)
                and user.node.node in epilogue_nodes
                for user in users
            )

        flag_template_buffer_has_other_users = template_buffer_has_other_users(
            ctb, template_node.outputs_by_name, epilogue_ir_nodes
        )
        kernel, render = ctb.make_kernel_render(  # type: ignore[misc]
            ctb,
            flag_template_buffer_has_other_users=flag_template_buffer_has_other_users,
            epilogue_nodes=epilogue_ir_nodes,
        )
        with kernel:
            if not is_multi_outputs_template(template_node.node):
                template_node.mark_run()  # type: ignore[attr-defined]
            for node in epilogue_nodes:
                node.mark_run()  # type: ignore[attr-defined]
            src_code = render()

        with V.set_kernel_handler(kernel):
            node_schedule = [template_node, *epilogue_nodes]
            kernel_name = self.define_kernel(src_code, node_schedule, kernel.args)

        if is_multi_outputs_template(template_node.node):
            # For multi outputs template, allocate buffers for each output after the epilogue
            # codegen to which determines if the buffer has been removed.
            assert len(template_node.outputs) == 1, (
                "Multi outputs template should be with 1 output template buffer of MultiOutputLayout"
            )
            for user in template_node.outputs[0].users:
                assert isinstance(user.node, ExternKernelSchedulerNode), (
                    "Multi outputs template should be with ExternKernelSchedulerNode"
                )
                assert isinstance(user.node.node, ir.MultiOutput), (
                    "Multi outputs template has multi users with MultiOutput"
                )
                user.node.mark_run()

        self.codegen_comment(node_schedule, kernel_name)
        kernel.call_kernel(kernel_name, ctb)
        V.graph.removed_buffers |= kernel.removed_buffers
        self.free_buffers_in_scheduler()