def linear(match, *args, **kwargs):
            graph = match.graph
            linear_node = match.output_node()
            input = args[0] if linear_node.target is aten.mm.default else args[1]
            bias = (
                None
                if linear_node.target is aten.mm.default
                or (
                    linear_node.target is aten.addmm.default
                    and linear_node.kwargs.get("beta", 1.0) == 0.0
                )
                else args[0]
            )
            weight = args[1] if linear_node.target is aten.mm.default else args[2]
            device_type = input.meta.get("val").device.type
            mkldnn_device_op = _get_mkldnn_device_op(device_type)
            with graph.inserting_before(linear_node):
                transpose_weight_node = graph.create_node(
                    "call_function", aten.permute.default, (weight, (1, 0))
                )
                weight_dtype = weight.meta.get("val").dtype
                is_lp_weight = weight_dtype in (
                    torch.bfloat16,
                    torch.float16,
                )
                reduced_f32_matmul_enabled = (
                    torch.backends.mkldnn.matmul.fp32_precision in ["bf16", "tf32"]  # type: ignore[attr-defined]
                )
                use_reduced_f32_for_fp32_weight = (
                    reduced_f32_matmul_enabled and weight_dtype == torch.float32
                )
                compute_with_lp = is_lp_weight or use_reduced_f32_for_fp32_weight
                batch_size = input.meta.get("val").shape[0]
                packed_weight_node = mkldnn_device_op.pack_linear_weight(
                    graph, compute_with_lp, transpose_weight_node, batch_size
                )
                packed_linear_node = mkldnn_device_op.pack_linear(
                    graph, compute_with_lp, batch_size, input, packed_weight_node, bias
                )

                linear_node.replace_all_uses_with(packed_linear_node)
                packed_linear_node.meta.update(linear_node.meta)
                graph.erase_node(linear_node)
            counters["inductor"]["mkldnn_linear_weight_pack_matcher_count"] += 1
            counters["inductor"]["mkldnn_linear_weight_pack_matcher_nodes"] += len(
                match.nodes
            )