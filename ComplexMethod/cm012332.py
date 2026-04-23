def _validate_pattern(match: Match):
        if len(match.nodes) not in [4, 5, 6, 7, 10]:
            return False
        # Make sure weight is a constant
        aten_int_mm_node = filter_nodes(match.nodes, aten._int_mm.default)[0]
        if not isinstance(aten_int_mm_node.args[1], torch.fx.node.Node):
            return False
        if aten_int_mm_node.args[1].op != "get_attr":
            return False

        if len(match.nodes) == 10:
            # Check the two tailing reshape nodes can be fused
            if match.nodes[9].args[1] != match.nodes[6].args[1]:
                return False
        if len(match.nodes) == 10 or (
            len(match.nodes) == 7 and match.nodes[6].target is aten.add.Tensor
        ):
            bias_idx = 7 if len(match.nodes) == 10 else 6
            # Check bias shape
            bias_node = match.nodes[bias_idx].args[1]
            if not isinstance(bias_node, torch.fx.node.Node):
                return False
            if len(bias_node.meta.get("tensor_meta").shape) != 1:  # type: ignore[union-attr]
                return False
        return True