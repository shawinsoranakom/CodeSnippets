def _can_use_buffer_overlap_scoring(
        self,
        node1: BaseSchedulerNode,
        node2: BaseSchedulerNode,
    ) -> bool:
        """
        Check if buffer overlap scoring should be used for this node pair.

        Buffer overlap scoring handles split/cat patterns where nodes read from
        the same buffer at different indices. We skip it when:
        - Either node is a reduction (different memory access patterns)
        - Either node is a template
        - Both nodes are prologue/epilogue candidates for the same template,
          because horizontal fusion would prevent them from being absorbed
          into the template kernel. For example, in:
            q = a[:64, :]; k = a[64:, :]
            return mm(q + 2, k - 2)
          "q + 2" and "k - 2" both read from `a` and would get a high overlap
          score, but fusing them horizontally prevents prologue fusion into mm
          (resulting in 2 kernels instead of 1).

        We allow buffer overlap scoring when:
        - The node outputs are not actually in the template's allowed_prologue_inps,
          meaning they can't be prologue-fused anyway, so horizontal fusion doesn't
          prevent any optimization opportunity.
        """
        if node1.is_reduction() or node2.is_reduction():
            return False
        if node1.is_template() or node2.is_template():
            return False

        if config.max_autotune or config.max_autotune_gemm:
            node1_outputs = node1.get_outputs()
            node2_outputs = node2.get_outputs()

            # Early return if either node has no outputs
            if not node1_outputs or not node2_outputs:
                return True

            node1_output_names = OrderedSet(buf.get_name() for buf in node1_outputs)
            node2_output_names = OrderedSet(buf.get_name() for buf in node2_outputs)

            # Find templates that consume node1's outputs via buffer users
            # and check if the outputs are actually prologue-fusable
            node1_prologue_eligible_template_users: OrderedSet[BaseSchedulerNode] = (
                OrderedSet()
            )
            for buf in node1_outputs:
                for user in buf.users:
                    if (
                        isinstance(user.node, BaseSchedulerNode)
                        and user.node.is_template()
                        and _is_prologue_fusion_enabled(user.node)
                    ):
                        # Check if this output is actually in the template's
                        # allowed_prologue_inps. If not, fusing horizontally
                        # won't prevent any prologue fusion opportunity.
                        template_node = user.node.get_template_node()
                        if template_node is not None and isinstance(
                            template_node, ir.TritonTemplateBuffer
                        ):
                            allowed_inps = template_node.get_allowed_prologue_inps()
                            if node1_output_names & allowed_inps:
                                node1_prologue_eligible_template_users.add(user.node)
                        else:
                            # Conservative: assume it could be a prologue candidate
                            node1_prologue_eligible_template_users.add(user.node)

            # Check if any of node1's prologue-eligible template users also consume
            # node2's outputs in a prologue-eligible way
            if node1_prologue_eligible_template_users:
                for buf in node2_outputs:
                    for user in buf.users:
                        if (
                            isinstance(user.node, BaseSchedulerNode)
                            and user.node.is_template()
                            and user.node in node1_prologue_eligible_template_users
                        ):
                            # Also verify node2's output is prologue-eligible
                            template_node = user.node.get_template_node()
                            if template_node is not None and isinstance(
                                template_node, ir.TritonTemplateBuffer
                            ):
                                allowed_inps = template_node.get_allowed_prologue_inps()
                                if node2_output_names & allowed_inps:
                                    return False
                            else:
                                # Conservative: block fusion
                                return False

            for node in (node1, node2):
                for dep in node.read_writes.reads:
                    producer = self.name_to_fused_node.get(dep.name)
                    if (
                        producer is not None
                        and producer.is_template()
                        and _is_epilogue_fusion_enabled(producer)
                    ):
                        return False

        return True