def remove_unused_sizes(self) -> set[int]:
        used_sizes = []
        unused_sizes = []

        # seek placeholder, should be at nodes[1]
        it = iter(self.fx_tracer.graph.nodes)
        next(it)
        sizes_node = next(it)
        assert sizes_node.name == "sizes"

        for getitem_node in sizes_node.users:
            assert getitem_node.target is operator.getitem
            if getitem_node.users:
                used_sizes.append(getitem_node)
            else:
                # remove from the graph
                unused_sizes.append(getitem_node)

        used_sizes_idx: set[int] = set()
        for used in used_sizes:
            assert isinstance(used.args, tuple)
            assert used.args[0] == sizes_node
            assert isinstance(used.args[1], int)
            next_size_idx = len(used_sizes_idx)
            # used later reindex the runtime sizes arg
            used_sizes_idx.add(used.args[1])
            # reindex the graph
            used.args = (used.args[0], next_size_idx)

        for unused in unused_sizes:
            self.fx_tracer.graph.erase_node(unused)

        return used_sizes_idx