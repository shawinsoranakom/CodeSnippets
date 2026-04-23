def is_contiguous_load(cls, buf: str, parent_node: BaseSchedulerNode) -> bool:
        from torch._inductor.loop_body import MemoryUsageType

        for node in parent_node.get_nodes():
            assert isinstance(node, SchedulerNode)
            loop_body = node._body
            entries = loop_body.memory_usage[MemoryUsageType.LOAD]
            index_names = [e.index_name for e in entries if e.buffer_name == buf]

            if len(index_names) == 0:
                continue

            # there can be multiple index_names some times
            for index_name in index_names:
                index_expr = loop_body.indexing_exprs[index_name]
                var_ranges = loop_body.var_ranges

                # assumes the final symbol is for reduction
                var_symbols = list(var_ranges.keys())
                stride_vars = V.graph.sizevars.stride_vars(
                    index_expr,
                    var_symbols,
                    var_symbols,
                )

                # stride==0 means a broadcast
                if not (stride_vars[-1] == 0 or stride_vars[-1] == 1):
                    return False
        return True