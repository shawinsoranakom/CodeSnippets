def group_batch_fusion_passes(graph: torch.fx.Graph, pre_grad=True):
    fusions: list[GroupBatchFusionBase] = []
    # we keep all current pre grad fusions to keep
    # current implementation, will remove this later
    if pre_grad:
        fusions += generate_fusion_from_config(
            config.pre_grad_fusion_options, pre_grad=True
        )
    else:
        fbgemm_fusion_keys = [
            x
            for x in config.post_grad_fusion_options
            if (
                x not in OPTIMUS_EXCLUDE_POST_GRAD
                and config.post_grad_fusion_options[x].get("require_fbgemm", False)
            )
        ]
        fbgemm_fusions = {
            fusion: config.post_grad_fusion_options[fusion]
            for fusion in fbgemm_fusion_keys
        }
        non_fbgemm_fusions = {
            fusion: config.post_grad_fusion_options[fusion]
            for fusion in config.post_grad_fusion_options
            if fusion not in fbgemm_fusion_keys
        }
        fusions += generate_fusion_from_config(non_fbgemm_fusions, pre_grad=False)
        if has_fbgemm:
            fusions += generate_fusion_from_config(fbgemm_fusions, pre_grad=False)

    for i, rule in enumerate(fusions):
        with GraphTransformObserver(
            graph.owning_module,
            f"group_batch_fusion_{i}",
        ):
            apply_group_batch_fusion(graph, rule)