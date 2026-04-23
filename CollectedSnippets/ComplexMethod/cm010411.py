def backward(
        ctx,
        *grad_outs,
    ):
        from torch._dynamo.utils import dynamo_timed

        subgraph = ctx._subgraph
        identifier = ctx._identifier
        output_metadata = ctx._output_metadata
        primals = saved_values(ctx)

        # Filter out grads that are None or do not require_grad. This was
        # the assumption we made during the tracing of joint_graph.
        filtered_grad_outs = []
        for idx, o in enumerate(grad_outs):
            if o is None:
                if idx not in output_metadata.indexes_with_symint:
                    raise AssertionError(
                        f"unexpected None grad_out at index {idx}, not in indexes_with_symint"
                    )
            elif idx in output_metadata.indexes_with_no_grad:
                # Deliberately skip over the grad_outs which we know should be
                # None because the corresponding fwd_out does not require_grad.
                pass
            else:
                filtered_grad_outs.append(o)
        filtered_grad_outs = tuple(filtered_grad_outs)

        # Important note - Even though the forward graph can be same for
        # different invoke_subgraphs, the backward graph can be different
        # because the tangent strides can be different. So, here we cache on
        # tangent_metadata in addition to identifier
        from torch._guards import detect_fake_mode
        from torch._subclasses._fake_tensor_utils import _CacheKeyState
        from torch._subclasses.fake_tensor import extract_tensor_metadata

        fake_mode = detect_fake_mode(primals + filtered_grad_outs)
        if fake_mode is None:
            raise AssertionError("fake_mode should be enabled for HOPs")
        state = _CacheKeyState(fake_mode.shape_env)

        tangent_metadata: list[object] = []
        for tangent in filtered_grad_outs:
            metadata = extract_tensor_metadata(tangent)
            metadata._flatten_into(tangent_metadata, fake_mode, state)

        # Add aliasing information to tangent_metadata
        # Two tangents are aliased if they are the same tensor object (using id())
        # We create a tuple of tuples where each inner tuple contains indices of aliased tensors
        # e.g. ((0, 1),) would mean there is one aliasing group, and the first and second tangents are aliased
        # e.g. () would mean there is no aliasing between tangents
        tensor_to_indices: dict[int, list[int]] = defaultdict(list)
        for i, tangent in enumerate(filtered_grad_outs):
            if isinstance(tangent, torch.Tensor):
                tensor_to_indices[id(tangent)].append(i)

        aliasing_groups = tuple(
            sorted(
                tuple(indices)
                for indices in tensor_to_indices.values()
                if len(indices) > 1
            )
        )
        tangent_metadata.append(aliasing_groups)

        # pyrefly: ignore [bad-assignment]
        tangent_metadata = tuple(tangent_metadata)

        # bw_graph is a joint graph with signature (*primals_and_tangents) and
        # returns (*grads_and_fw_outs). To get the grads, we use the num_fw_outs
        # to extract the grads.
        primals_and_tangents = primals + filtered_grad_outs

        # Check if we have already traced the bwd subgraph.
        bw_graph = None
        suffix = None
        invoke_subgraph_cache = get_invoke_subgraph_cache()
        cache_hit = False
        if invoke_subgraph_cache:
            bw_graph, suffix = invoke_subgraph_cache.get_lazy_bwd_entry(
                identifier, tangent_metadata
            )
            cache_hit = bw_graph is not None

        if bw_graph is None:
            if suffix is not None:
                raise AssertionError(
                    f"suffix should be None when bw_graph is None, got {suffix}"
                )
            with dynamo_timed(
                "invoke_subgraph_trace_joint_graph", log_pt2_compile_event=True
            ):
                bw_graph = trace_joint_graph_as_bwd(
                    subgraph,
                    len(primals),
                    primals_and_tangents,
                    ctx._fw_include_key_set,
                    ctx._fw_exclude_key_set,
                )
                if (
                    hasattr(subgraph, "meta")
                    and "nested_region_config" in subgraph.meta
                ):
                    bw_graph.meta["nested_region_config"] = subgraph.meta[
                        "nested_region_config"
                    ]

        if invoke_subgraph_cache and not cache_hit:
            suffix = invoke_subgraph_cache.add_lazy_bwd_entry(
                identifier, tangent_metadata, bw_graph
            )

        grads = invoke_subgraph(
            bw_graph, f"bw_{identifier}_{suffix}", *primals_and_tangents
        )[: -output_metadata.num_fw_outs]
        return None, None, None, *grads