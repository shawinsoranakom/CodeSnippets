def _get_indexing_ranges_exprs(self, node):
        if isinstance(node, FusedSchedulerNode):
            assert len(node.snodes) > 0, node.snodes
            var_ranges = None
            indexing_exprs = OrderedSet[Any]()
            for snode in node.snodes:
                v, exprs = self._get_indexing_ranges_exprs(snode)
                if var_ranges is None:
                    var_ranges = v
                assert var_ranges == v, (var_ranges, v, node.snodes)
                indexing_exprs.update(exprs)
            return var_ranges, list(indexing_exprs)

        assert isinstance(node, SchedulerNode)
        comp_buffer = node.node
        assert isinstance(comp_buffer, ir.ComputedBuffer)
        _, body, _ = comp_buffer.get_default_sizes_body()
        return body.var_ranges, list(body.indexing_exprs.values())