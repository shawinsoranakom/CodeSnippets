def get_expand_dim_for_pointwise_nodes(
        self, node1: BaseSchedulerNode, node2: BaseSchedulerNode
    ) -> tuple[int, SchedulerNode, sympy.Expr] | None:
        """
        Fusing two small pointwise nodes significantly reduces kernel overhead
        and launch overhead. However, slightly different sizes would prevent fusion.
        Here, we decide if expanding sizes of one node is profitible by allowing
        fusion, and returns the dimension to expand, node with smaller sizes,
        and new size after expand.
        """
        # only support scheduler node
        if not isinstance(node1, SchedulerNode) or not isinstance(node2, SchedulerNode):
            return None

        # only support computued buffer
        if not (
            isinstance(node1.node, ir.ComputedBuffer)
            and isinstance(node2.node, ir.ComputedBuffer)
        ):
            return None

        # does not support mutation yet since relying on index mod to handle
        # out-of-boundary access.
        if node1.has_aliasing_or_mutation() or node2.has_aliasing_or_mutation():
            return None

        # skip halide which does not support mod for index
        if config.cpu_backend == "halide":
            return None

        # only support pointwise nodes with the same reduction size
        n1_sizes, n2_sizes = node1._sizes, node2._sizes
        n1_iter_sizes, n1_reduce_sizes = n1_sizes
        n2_iter_sizes, n2_reduce_sizes = n2_sizes
        if (
            node1.is_reduction()
            or node2.is_reduction()
            or n1_reduce_sizes != n2_reduce_sizes
            or len(n1_iter_sizes) != len(n2_iter_sizes)
        ):
            return None

        # only support nodes with 1 write for simplification
        if len(node1.read_writes.writes) > 1 or len(node2.read_writes.writes) > 1:
            return None

        # When memory access is small, reducing gpu kernel overhead is profitable over
        # slightly larger memory access.
        node1_write_memory = self.dep_size_hint(next(iter(node1.read_writes.writes)))
        node2_write_memory = self.dep_size_hint(next(iter(node1.read_writes.writes)))
        if (
            max(node1_write_memory, node2_write_memory)
            > config.small_memory_access_threshold
        ):
            return None

        # does not support reinplace since `index % boundary` may lead to
        # race condition
        def has_reusable_buffer(node: BaseSchedulerNode) -> bool:
            for read in node.read_writes.reads:
                input_buf: SchedulerBuffer | SchedulerDonatedBuffer | None
                if read.name in self.name_to_donated_buffer:
                    input_buf = self.name_to_donated_buffer[read.name]
                else:
                    input_buf = self.name_to_buf.get(read.name)

                if (
                    input_buf
                    and V.graph.wrapper_code.can_reuse(input_buf, node)
                    and not isinstance(input_buf.defining_op, NopKernelSchedulerNode)
                ):
                    return True
            return False

        if has_reusable_buffer(node1) or has_reusable_buffer(node2):
            return None

        # only support nodes with 1 mismatch dimension
        mismatch_dimensions = []
        for idx, (n1_size, n2_size) in enumerate(zip(n1_iter_sizes, n2_iter_sizes)):
            if n1_size != n2_size:
                mismatch_dimensions.append(idx)

        if len(mismatch_dimensions) != 1:
            return None

        mismatch_dim = mismatch_dimensions[0]
        mismatch_size1, mismatch_size2 = (
            n1_iter_sizes[mismatch_dim],
            n2_iter_sizes[mismatch_dim],
        )
        if V.graph.sizevars.statically_known_lt(mismatch_size1, mismatch_size2):
            return mismatch_dim, node1, mismatch_size2
        elif V.graph.sizevars.statically_known_lt(mismatch_size2, mismatch_size1):
            return mismatch_dim, node2, mismatch_size1
        else:
            return None