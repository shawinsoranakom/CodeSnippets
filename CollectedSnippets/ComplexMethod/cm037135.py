def __call__(self, graph: torch.fx.Graph) -> None:
        count = 0
        # Remove no-op reshapes/views:
        for node in graph.nodes:
            if is_func(node, torch.ops.aten.reshape.default):
                # Case 1: rewrite reshape chains to reshapes on the base tensor
                input = node.args[0]
                # If the input is a reshape, rebind to that node
                if is_func(input, torch.ops.aten.reshape.default):
                    # The new input is guaranteed not to be a reshape,
                    # because we process nodes in order
                    node.update_arg(0, input.args[0])
                    if len(input.users) == 0:
                        graph.erase_node(input)
                        count += 1

            # remove reshape/slice if it produces the original shape
            if is_func(node, torch.ops.aten.reshape.default) or is_func(
                node, torch.ops.aten.slice.Tensor
            ):
                input = node.args[0]
                input_shape = input.meta["val"].shape
                output_shape = node.meta["val"].shape
                if self.all_dims_equivalent(input_shape, output_shape):
                    node.replace_all_uses_with(input)
                    graph.erase_node(node)
                    count += 1
            elif is_func(node, torch.ops.aten.slice_scatter.default):
                base, view, dim_index, start, end = node.args[:5]
                base_shape = base.meta["val"].shape
                view_shape = view.meta["val"].shape

                if self.all_dims_equivalent(base_shape, view_shape):
                    node.replace_all_uses_with(view)
                    graph.erase_node(node)
                    count += 1

        logger.debug("Removed %s no-op reshapes and slices", count)