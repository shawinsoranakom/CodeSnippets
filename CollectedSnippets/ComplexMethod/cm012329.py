def _inner(match):
        # Check dequant pattern has only 1 user.
        (
            linear_node,
            _,
        ) = _get_linear_node(match, input_dim_exceeds_two, input_contiguous)

        input_index = 1 if linear_node.target is aten.addmm.default else 0
        assert dtype in [torch.float32, torch.bfloat16]
        (
            dequant_node,
            _,
            _,
            _,
        ) = _get_linear_dq_node(
            linear_node,
            input_index,
            input_dim_exceeds_two,
            input_contiguous,
            with_dtype_convert,
        )

        assert dequant_node.target in [
            quantized_decomposed.dequantize_per_tensor.default,
            quantized_decomposed.dequantize_per_tensor.tensor,
        ]

        if len(list(dequant_node.users)) != 1:
            # Ensure the dequant pattern only has 1 user
            # since we will delete the dequant pattern here
            return False

        # Extra check for bmm pattern
        if input_dim_exceeds_two and not input_contiguous:
            # Check for act
            # Act expand size should be exactly same as act size
            act_expand_size = match.kwargs["act_expand_size"]
            act_node = match.kwargs["x"]
            if not (
                hasattr(act_node, "meta")
                and isinstance(act_node.meta.get("val", None), torch.Tensor)
                and (act_node.meta["val"].size() == torch.Size(act_expand_size))
            ):
                return False

            # Check for wgt
            # wgt permute dims should be [1, 0]
            wgt_permute_dims = match.kwargs["permute_axes"]
            if wgt_permute_dims != [1, 0]:
                return False

            # Check below wgt size items:
            # wgt before expand should with dim 2
            # Expand size should with dim 3
            # Expand size[0] should same as act size[0]
            # Expand size[1] should same as wgt size[1]
            # Expand size[2] should same as wgt size[0]
            qweight_node = match.kwargs["q_weight"]
            wgt_expand_size = match.kwargs["wgt_expand_size"]
            if not (
                hasattr(qweight_node, "meta")
                and isinstance(qweight_node.meta.get("val", None), torch.Tensor)
                and len(qweight_node.meta["val"].size()) == 2
                and len(wgt_expand_size) == 3
                and wgt_expand_size[0] == act_node.meta["val"].size()[0]
                and wgt_expand_size[1] == qweight_node.meta["val"].size()[1]
                and wgt_expand_size[2] == qweight_node.meta["val"].size()[0]
            ):
                return False

        return True