def pre_grad_passes(
    gm: torch.fx.GraphModule,
    example_inputs: Sequence[object] = (),
    add_passes: str | None = None,
    remove_passes: str | None = None,
) -> torch.fx.GraphModule:
    """
    Apply passes on the input FX graph using Torch IR.

    WARNING:
    The IR before grad is not functional or normalized, so it is harder
    to write passes on this IR.  Passes must be safe with respect to
    aliasing and mutation and need to handle all possible arg schemas.

    Consider adding a new pass to post_grad.py or joint_graph.py which
    are after functionalization and normalization.
    """
    if config.pattern_matcher:
        lazy_init()
        if hasattr(
            config, "fx_passes_numeric_check"
        ) and config.fx_passes_numeric_check.get("pre_grad", False):
            gm_before_fx_passes = gm.__copy__()
        # explicitly run with predispatch atenIR based passes
        if config.is_predispatch:
            _run_pre_dispatch_passes(gm, example_inputs, add_passes, remove_passes)
        else:
            # We only log the graph with changes to avoid the excessive compilation time
            # https://fb.workplace.com/groups/257735836456307/permalink/633533465543207/
            if example_inputs is not None:
                gm = fuse_fx(gm, example_inputs)
            numpy_compat_normalization(gm.graph)
            # We should always do the normalization_pass first
            if "normalization_pass" in config.pre_grad_fusion_options:
                pattern_matcher_pass = PRE_GRAD_PATTERNS["normalization_pass"]
                pattern_matcher_pass.apply(gm.graph)  # type: ignore[arg-type]
            GraphTransformObserver(gm, "group_batch_fusion_passes").apply_graph_pass(
                lambda graph: group_batch_fusion_passes(graph, pre_grad=True)
            )
            for pass_name in config.pre_grad_fusion_options:
                # skip all patterns for group batch fusions
                if pass_name in PRE_GRAD_FUSIONS or pass_name == "normalization_pass":
                    continue
                pattern_matcher_pass = PRE_GRAD_PATTERNS[pass_name]
                inductor_before_change = save_inductor_dict(
                    [pattern_matcher_pass.pass_name]
                )
                # we support run same pattern multiple times, the default is to run only once
                counter = config.pre_grad_fusion_options[pass_name].get("counter", 1)
                for _ in range(counter):
                    pattern_matcher_pass.apply(gm.graph)  # type: ignore[arg-type]
                if not is_same_dict(counters["inductor"], inductor_before_change):
                    trace_structured(
                        "artifact",
                        metadata_fn=lambda: {
                            "name": f"{pattern_matcher_pass.pass_name}_pre_grad",
                            "encoding": "string",
                        },
                        payload_fn=lambda: gm.print_readable(
                            print_output=False, include_stride=True, include_device=True
                        ),
                    )
            # TODO: move efficient_conv_bn_eval_pass to the fusions dict too.
            GraphTransformObserver(gm, "efficient_conv_bn_eval_pass").apply_graph_pass(
                efficient_conv_bn_eval_pass.apply
            )
            GraphTransformObserver(gm, "apply_gumbel_max_trick_pass").apply_graph_pass(
                apply_gumbel_max_trick_pass.apply
            )

    if config.pre_grad_custom_pass is not None:
        GraphTransformObserver(gm, "pre_grad_custom_pass").apply_graph_pass(
            config.pre_grad_custom_pass
        )

    stable_topological_sort(gm.graph)

    from .quantization import quant_lift_up

    quant_lift_up(gm)

    gm.graph.lint()
    gm.recompile()

    if (
        config.pattern_matcher
        and hasattr(config, "fx_passes_numeric_check")
        and config.fx_passes_numeric_check.get("pre_grad", False)
        and example_inputs is not None
    ):
        from .numeric_utils import numeric_check_if_enabled

        gm_after_fx_passes = gm.__copy__()
        numeric_check_if_enabled(
            gm_before_fx_passes,  # type: ignore[possibly-undefined]
            gm_after_fx_passes,
            example_inputs,
            config.fx_passes_numeric_check.get("num_iterations", 1),
            config.fx_passes_numeric_check.get("precision", 1e-4),
        )

    return gm