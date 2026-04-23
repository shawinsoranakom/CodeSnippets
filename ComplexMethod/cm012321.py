def fn(match):
        output_dtype = _get_pattern_output_dtype(match)
        compute_node = filter_nodes(match.nodes, qop)[0]
        # qop_pointwise should only have one user
        if len(compute_node.users) != 1:
            return False
        binary_node_inputs = next(iter(compute_node.users)).args
        assert len(binary_node_inputs) == 2, "Expects binary node with 2 inputs"
        if output_dtype in [torch.float32, torch.bfloat16]:
            extra_input_of_binary_node = None
            for arg in binary_node_inputs:
                if arg != compute_node:
                    extra_input_of_binary_node = arg
                    break
            assert extra_input_of_binary_node is not None
            # Extra input of binary node comes from dequant pattern
            if extra_input_from_dequant and (
                (not isinstance(extra_input_of_binary_node, torch.fx.Node))
                or (
                    extra_input_of_binary_node.target
                    != quantized_decomposed.dequantize_per_tensor.default
                )
            ):
                return False

        # the two inputs of binary node should have attribute "meta" and should be tensors
        if not (
            hasattr(binary_node_inputs[0], "meta")
            and isinstance(binary_node_inputs[0].meta.get("val", None), torch.Tensor)  # type: ignore[union-attr]
        ) or not (
            hasattr(binary_node_inputs[1], "meta")
            and isinstance(binary_node_inputs[1].meta.get("val", None), torch.Tensor)  # type: ignore[union-attr]
        ):
            return False
        # the two inputs of binary node should have the same shape
        if (
            binary_node_inputs[0].meta["val"].size()  # type: ignore[union-attr]
            != binary_node_inputs[1].meta["val"].size()  # type: ignore[union-attr]
        ):
            return False

        # All users of the extra input in this pattern should be
        # ancestor nodes of the compute node, except for the binary node
        # connected to the compute node.

        from .mkldnn_fusion import _get_remaining_users

        extra_input_of_pattern = (
            match.kwargs["other"]
            if "other" in match.kwargs
            else (
                match.kwargs["accum"]
                if (output_dtype in [torch.uint8, torch.int8])
                or (not extra_input_from_dequant)
                else match.kwargs["accum_after_dequant"]
            )
        )
        if (
            len(_get_remaining_users(extra_input_of_pattern, compute_node)) > 1
            or extra_input_of_pattern == compute_node.args[0]
        ):
            return False
        return True