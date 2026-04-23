def _addmm_node_can_be_fused(self, node: torch.fx.Node):
        input_shape = node.args[1].meta["val"].shape  # type: ignore[union-attr]
        weight_shape = node.args[2].meta["val"].shape  # type: ignore[union-attr]
        return (
            node.kwargs.get("beta", DEFAULT_BETA) == DEFAULT_BETA
            and node.kwargs.get("alpha", DEFAULT_ALPHA) == DEFAULT_ALPHA
            and len(input_shape) == 2
            and len(weight_shape) == 2
            and all(x % 2 == 0 for x in input_shape + weight_shape)
            and all(
                shape <= self.graph_search_options["max_fuse_tensor_size_group_linear"]
                for shape in input_shape + weight_shape
            )
        )