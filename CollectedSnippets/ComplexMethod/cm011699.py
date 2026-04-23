def decide_inplace_update(self) -> None:
        """
        Decide if there should be inplace updates for the node
        and record the decision in the active kernel.
        """
        from .codegen.wrapper import can_match_buffer_size

        if not (
            isinstance(self, SchedulerNode)
            and config.inplace_buffers
            and V.graph.has_feature(self.get_device(), BackendFeature.INPLACE_BUFFERS)
            and (
                not isinstance(V.kernel, torch._inductor.codegen.simd.SIMDKernel)
                or getattr(V.kernel, "mutations", None) is not None
            )
            # hacky check for if V.kernel is a real kernel or NullHandler
            and hasattr(V.kernel, "args")
        ):
            return

        # NOTE remove V.graph.removed_operations once deps issue is fixed
        inconsequential_nodes = (
            self.ancestors
            | V.graph.removed_operations
            | self.scheduler.completed_operations
        )

        def single_index_in_fused_node(buf_to_be_inplaced: SchedulerBuffer) -> bool:
            # Inside of NodeUser, we track that the read and write are equivalent
            # before deciding if the use can be inplace.
            # But if that use is fused into a larger kernel, we need to check equivalence
            # of other accesses in fused scheduler node as well.
            fused_node = buf_to_be_inplaced.scheduler.get_fused_node(self)
            buf_name = buf_to_be_inplaced.get_name()
            # Dedup read/writes with equivalent indices
            # TODO - would be nice if we could just cache accesses on ReadWrites,
            # and enforce variant that this class & members are functional..
            deps: OrderedSet[Dep] = OrderedSet()
            for user in buf_to_be_inplaced.users:
                user_node = user.node
                if not isinstance(user_node, BaseSchedulerNode):
                    continue

                if (
                    user_node.get_first_name()
                    not in buf_to_be_inplaced.scheduler.name_to_fused_node
                    or buf_to_be_inplaced.scheduler.get_fused_node(user_node)
                    is not fused_node
                ):
                    continue

                deps |= (
                    o
                    for o in user_node.read_writes.reads_and_writes()
                    if o.name == buf_name
                )
                if len(deps) > 1:
                    return False

            return True

        for buf in self.get_outputs():
            buf_node = buf.node
            assert buf_node is not None
            if (
                not buf_node.should_allocate()
                or buf_node.get_inputs_that_alias_output()
                or buf_node.get_mutation_names()
                or buf.get_name() in V.graph.removed_buffers
                # CommBufferLayout buffer must keep its P2P allocation.
                # Do not allow in-place reuse into or from a P2P buffer.
                or isinstance(buf_node.get_output_spec(), ir.CommBufferLayout)
            ):
                continue

            for read in self.read_writes.reads:
                input_buf: SchedulerBuffer | SchedulerDonatedBuffer | None
                if read.name in self.scheduler.name_to_donated_buffer:
                    input_buf = self.scheduler.name_to_donated_buffer[read.name]
                else:
                    input_buf = self.scheduler.name_to_buf.get(read.name)

                if (
                    input_buf
                    and V.graph.wrapper_code.can_reuse(input_buf, self)
                    and not isinstance(input_buf.defining_op, NopKernelSchedulerNode)
                ):
                    assert input_buf.users is not None
                    remaining_uses = [
                        x
                        for x in input_buf.users
                        if x.node.get_name() not in inconsequential_nodes
                    ]
                    has_cross_stream_hazard = self.scheduler.has_cross_stream_hazard(
                        read.name, self
                    )

                    if (
                        not has_cross_stream_hazard
                        and len(remaining_uses) == 1
                        and remaining_uses[0].can_inplace
                        and remaining_uses[0].node is self
                        and input_buf.node is not None
                        and not isinstance(
                            input_buf.node.get_output_spec(),
                            (
                                ir.NoneLayout,
                                ir.MultiOutputLayout,
                                ir.MutationLayoutSHOULDREMOVE,
                                ir.CommBufferLayout,
                            ),
                        )
                        and not (
                            input_buf.defining_op
                            and isinstance(
                                input_buf.defining_op.node,
                                (ir.FallbackKernel, ir.MultiOutput),
                            )
                            and len(input_buf.node.get_inputs_that_alias_output()) > 0
                        )
                        and can_match_buffer_size(input_buf.node, buf.node)
                        and single_index_in_fused_node(input_buf)
                    ):
                        # if there isn't a triton kernel, then we don't need to call triton-specific things.
                        # but TODO this might be a convenient place to signal to the Collective kernels to inplace
                        # (and, can we make "kernel" less generic of a name?)
                        V.kernel.args.make_inplace(input_buf.get_name(), buf.get_name())
                        # mutations not tracked in cpp kernels
                        if isinstance(
                            V.kernel, torch._inductor.codegen.simd.SIMDKernel
                        ):
                            V.kernel.mutations.add(input_buf.get_name())
                            V.kernel.mutations.add(buf.get_name())

                        V.kernel.inplace_update_buffers[buf.get_name()] = (
                            input_buf.get_name()
                        )
                        break