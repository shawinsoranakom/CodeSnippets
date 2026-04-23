def propagate_addmm_bwd() -> PropagateStatus:
        assert isinstance(bias_node, Node)
        assert isinstance(input_node, Node)
        assert isinstance(weight_node, Node)

        if not (meta := get_chunking_meta(addmm_node)):
            return PropagateStatus.SUCCEED_NO_CHANGE

        if meta.chunked_by_dim(0):
            # if the output is chunked by the batch dimension, then
            # bias and input should as well
            changed = set_chunking_meta(input_node, meta) | set_chunking_meta(
                weight_node
            )

            # We should chunk the bias only if it's not broadcasted
            bias_node_ft = get_fake_tensor_from_node_arg(bias_node)
            input_node_ft = get_fake_tensor_from_node_arg(input_node)
            assert bias_node_ft is not None
            assert input_node_ft is not None
            if bias_node_ft.ndim < input_node_ft.ndim:
                changed |= set_chunking_meta(bias_node)
            else:
                changed |= set_chunking_meta(bias_node, meta)
            return _bool_to_status(changed)

        return PropagateStatus.FAIL