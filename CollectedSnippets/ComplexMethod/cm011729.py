def decide_fusion_fail_reason(
        self,
        node1: BaseSchedulerNode,
        node2: BaseSchedulerNode,
        common_buf_names: tuple[str, ...] | OrderedSet[str],
    ) -> str:
        """
        Try to decide reasons why fusion fail due to no shared memory even though
        there are common buffers.
        """
        reasons = {}
        node1_name2dep = {dep.name: dep for dep in node1.read_writes.reads_and_writes()}
        node2_name2dep = {dep.name: dep for dep in node2.read_writes.reads_and_writes()}

        for buf_name in common_buf_names:
            buf = V.graph.get_buffer(buf_name)
            lhs_dep = node1_name2dep[buf_name]
            rhs_dep = node2_name2dep[buf_name]

            if not isinstance(lhs_dep, MemoryDep) or not isinstance(rhs_dep, MemoryDep):
                reasons[buf_name] = (
                    f"not MemoryDep: {type(lhs_dep)} v.s. {type(rhs_dep)}"
                )
                continue

            if lhs_dep.get_numel() != rhs_dep.get_numel():
                reasons[buf_name] = (
                    f"different numel: {lhs_dep.get_numel()} v.s. {rhs_dep.get_numel()}"
                )
                continue

            # same numel but different MemoryDep.size. Should be broadcasting
            if sympy_product(lhs_dep.size) != sympy_product(rhs_dep.size):
                reasons[buf_name] = "broadcast"
                continue

            lhs_off = lhs_dep.get_offset()
            rhs_off = rhs_dep.get_offset()
            if lhs_off != rhs_off:
                # One example is in transformer, we use a concatenated linear layer
                # to project Q/K/V and then split the result. The 3 splits will
                # point to the same buffer with different offsets.
                reasons[buf_name] = f"different offset: {lhs_off} v.s. {rhs_off}"
                continue

            if (
                lhs_dep.normalize_with_stride_order()
                == rhs_dep.normalize_with_stride_order()
            ):
                reasons[buf_name] = f"Mismatch loop orders: {lhs_dep} v.s. {rhs_dep}"
                continue

            # Add more rules here
            layout_str = ""
            if not isinstance(buf, ir.TorchBindObject):
                layout_str = f"Layout: {buf.layout}"
            reasons[buf_name] = (
                f"Unknown reason: {lhs_dep} v.s. {rhs_dep}. {layout_str}"
            )

        return str(reasons)