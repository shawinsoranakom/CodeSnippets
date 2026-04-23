def can_fuse(
        self,
        node1: BaseSchedulerNode,
        node2: BaseSchedulerNode,
        can_reorder: bool = False,
        allow_mix_order_reduction: bool = True,
    ) -> bool:
        """
        Determine if it is possible to combine node1 and node2 into a
        single fused node.
        """
        if node1 is node2:
            return False

        # Prevent fusion across stream boundaries
        if self._has_multi_stream_nodes():
            stream1 = self.node_to_stream.get(node1)
            stream2 = self.node_to_stream.get(node2)
            if stream1 is not None and stream2 is not None and stream1 != stream2:
                return False

        if isinstance(node1, FusedMixOrderReductions):
            return node1.can_fuse_with(node2)
        if isinstance(node2, FusedMixOrderReductions):
            # We don't fuse something before a FusedMixOrderReductions
            # right now
            return False

        why = WhyNoFuse(node1, node2)

        if node1.is_template() and self.get_backend(
            node1.get_device()
        ).can_fuse_multi_outputs_template(node1, node2):
            return True

        if isinstance(node1, GroupedSchedulerNode) or isinstance(
            node2, GroupedSchedulerNode
        ):
            why("grouped node must not be fused with other nodes")
            return False
        if isinstance(node1, NopKernelSchedulerNode) and not node1.is_template():
            why("node1 is nop")
            return False

        if isinstance(node1, ExternKernelSchedulerNode):
            if not isinstance(node1.node, ir.UserDefinedTritonKernel):
                why("node1 is extern but not a triton kernel")
                return False

            if not node1.node.can_fuse_epilogue():
                why("node1's triton kernel doesn't support epilogue fusion")
                return False

            if not isinstance(node2, SchedulerNode):
                why("node1 is extern but node2 is not SchedulerNode")
                return False
            if not isinstance(node2.node, ComputedBuffer):
                why("node1 is extern but node2.node is not SchedulerNode")
                return False
            if not isinstance(node2.node.data, Pointwise):
                why("node1 is extern but node2.node.data is not Pointwise")
                return False

            assert len(node1.node.mutation_outputs) == 1
            written_buffer_name = node1.node.mutation_outputs[0].name

            # The epilogue can only read from the output buffer.
            # Any other tensor/s would require additional load expressions.
            if any(dep.name != written_buffer_name for dep in node2.read_writes.reads):
                why("epilogue reads from buffers other than the mutated output")
                return False

            # the epilogue depends on expressions which may not available in the user triton kernel
            # (e.g. indexing exprs used not in a load)
            node2_inner_fn_free_symbols = node2.node.data.inner_fn_free_symbols()
            for symbol in node2_inner_fn_free_symbols:
                usages = node2.node.data.collect_inner_fn_symbol_usage(symbol)
                if any(usage != "load" for usage in usages):
                    return False

            # should be true now because we checked `can_fuse_epilogue`
            assert len(node1.node.mutable_args) == 1
            if node1.node.mutable_args[0].layout != node2.node.layout:
                why("node1 and node2 uses different buf layouts")
                return False

            def _is_other_node_that_references_mutation_buffer(
                other_node: BaseSchedulerNode,
            ):
                return (
                    (other_node is not node1)
                    and (other_node is not node2)
                    and written_buffer_name in other_node.used_buffer_names()
                )

            if any(
                _is_other_node_that_references_mutation_buffer(node)
                for node in self.nodes
            ):
                return False

        if (
            isinstance(node2, (ExternKernelSchedulerNode, NopKernelSchedulerNode))
            and not node2.is_template()
        ):
            why("node2 is extern or nop")
            return False

        if node2.get_operation_names() & node1.ancestors:
            why("node1 must go before node2")
            return False

        if node2.is_template():
            if not _is_prologue_fusion_enabled(node2):
                why("prologue fusion turned off")
                return False

            if node1.is_reduction() or node1.is_template():
                why("prologue fusion only supported for pointwise nodes")
                return False

            template = node2.get_template_node_or_throw()
            allowed_prologue_inps = template.get_allowed_prologue_inps()
            if not allowed_prologue_inps:
                why("template has no allowed prologue inputs")
                return False

            unsupported_prologue_args = (
                OrderedSet(inp.get_name() for inp in template.inputs)  # type: ignore[union-attr]
                - allowed_prologue_inps
            )

            if node1.get_buffer_names() & unsupported_prologue_args:
                why("prologue fusion not implemented for kernel for these inputs")
                return False

            if node1.has_aliasing_or_mutation() or node1.has_aliasing_or_mutation():
                why("template prologue can only fuse functional pointwise nodes")
                return False

            prologue_nodes = node1.get_nodes()
            for node in prologue_nodes[:-1]:
                node_outs = node.get_outputs()
                for out in node_outs:
                    if not all(user.node in prologue_nodes for user in out.users):
                        why("template prologue can only fuse nodes with a single use")
                        return False

            template_snodes = (
                [node2]
                if not isinstance(node2, FusedSchedulerNode)
                else [n for n in node2.snodes if n.is_template()]
            )
            assert len(template_snodes) == 1
            template_snode = template_snodes[0]

            if not (
                len(prologue_nodes[-1].outputs) == 1
                and len(prologue_nodes[-1].outputs[0].users) == 1
                and prologue_nodes[-1].outputs[0].users[0].node is template_snode
            ):
                why(
                    "template prologue can only fuse nodes with a single use into template"
                )
                return False

            if not self.check_prologue_fusion_heuristics_fusable(node1, node2, why):
                return False

        if node1.is_template():
            if (
                node2.has_aliasing_or_mutation()
                or node2.is_reduction()
                or not _is_epilogue_fusion_enabled(node1)
            ):
                why("template epilogue not satisfied")
                return False
            template_buf = node1.get_template_node()
            assert template_buf is not None
            if template_buf.is_multi_outputs_template() and not isinstance(
                node2.node, ir.ComputedBuffer
            ):
                why("multi-output template epilogue requires ComputedBuffer")
                return False

        if (node1.get_buffer_names() & V.graph.no_fuse_buffer_names) or (
            node2.get_buffer_names() & V.graph.no_fuse_buffer_names
        ):
            why("fusion for buffer explicit disabled")
            return False
        device = node1.get_device()
        device2 = node2.get_device()
        if device != device2:
            why("device mismatch (%s vs %s)", device, device2)
            return False
        del device2

        shared_data_score = self.score_fusion_memory(
            node1, node2, allow_mix_order_reduction=allow_mix_order_reduction
        )
        assert isinstance(shared_data_score, int)

        if (
            can_reorder
            and shared_data_score < config.score_fusion_memory_threshold
            and (
                config.loop_ordering_after_fusion or config.loop_reindexing_after_fusion
            )
        ):
            new_shared_data_score = self.shared_data_after_reordering_loop(node1, node2)
            if new_shared_data_score >= 0:
                shared_data_score = new_shared_data_score

        if config.expand_dimension_for_pointwise_nodes and (
            expand_analysis := self.get_expand_dim_for_pointwise_nodes(node1, node2)
        ):
            (expand_dim, smaller_node, expand_size) = expand_analysis
            smaller_node.expand_dimension_for_pointwise_node(expand_dim, expand_size)
            shared_data_score = self.score_fusion_memory(node1, node2)
            assert isinstance(shared_data_score, int)

        if (
            config.loop_index_inversion_in_fusion
            and shared_data_score < config.score_fusion_memory_threshold
        ):
            new_shared_data_score = self.shared_data_after_inverting_indexing(
                node1, node2
            )
            if new_shared_data_score >= 0:
                shared_data_score = new_shared_data_score

        if loop_ordering_log.isEnabledFor(logging.DEBUG):
            loop_ordering_log.debug(
                "%s and %s has %s shared data",
                node1.get_name(),
                node2.get_name(),
                shared_data_score,
            )

        if not V.choices.can_fuse(self, node1, node2, shared_data_score):
            return False

        if node1.get_operation_names() & node2.ancestors:
            # node2 depends on node1 outputs
            return (
                self.can_fuse_vertical(node1, node2)
                and V.choices.can_fuse_vertical(self, node1, node2, shared_data_score)
                and self.get_backend(device).can_fuse_vertical(node1, node2)
            )
        else:  # nodes don't depend on each other, but may have common reads
            return V.choices.can_fuse_horizontal(
                self, node1, node2, shared_data_score
            ) and self.get_backend(device).can_fuse_horizontal(node1, node2)