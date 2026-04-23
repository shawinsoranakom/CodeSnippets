def create_compiler_config_extra(
    gm: GraphModule | GmWrapper,
) -> CompilerConfigExtra:
    gm_meta = gm.meta if isinstance(gm, GraphModule) else None

    # Although cudagraphs may have been enabled via config, various
    # conditions (which are tested within the bowels of Inductor) may
    # force cudagraphs to be disabled.  This mutable box lets us retrieve
    # the final determination if cudagraphs actually can be used or not.
    cudagraphs = BoxedBool(config.triton.cudagraphs)

    cudagraphs_bwd_override: bool | None = None

    # Override cudagraphs BoxedBool based on override_cudagraphs annotation.
    # Disabling fwd disables bwd (copying activations isn't profitable),
    # so cudagraphs_bwd_override is only needed for fwd=True / bwd=False.
    if (
        gm_meta is not None
        and (annotation := gm_meta.get("cudagraph_annotation")) is not None
    ):
        if annotation.fwd is not None and annotation.fwd != config.triton.cudagraphs:
            cudagraphs = BoxedBool(annotation.fwd)
            if annotation.fwd:
                cudagraphs_log.info(
                    "enabling cudagraphs due to override_cudagraphs annotation"
                )
            else:
                log_cudagraph_skip_and_bump_counter(
                    "disabling cudagraphs due to override_cudagraphs annotation"
                )

        # bwd override only matters when fwd enables cudagraphs but bwd
        # explicitly disables them.
        if cudagraphs.value and annotation.bwd is not None and not annotation.bwd:
            cudagraphs_bwd_override = annotation.bwd
            log_cudagraph_skip_and_bump_counter(
                "disabling cudagraphs for backward due to override_cudagraphs annotation"
            )

    # TODO: The modern style is to use CompileId from TracingContext to
    # identify Inductor compilation.  However, this CompileId cannot
    # uniquely identify multiple Inductor compilations that arise from
    # DDPOptimizer
    graph_id = next(_graph_counter)

    # See [Backward Generation Handling]
    forward_device = BoxedDeviceIndex(None)

    # Set by the forward compilation when it is partitioned for CUDA graphs.
    # The backward reads this to decide whether saved tensors can be assumed
    # to have fixed addresses.
    forward_is_partitioned = BoxedBool(False)

    return CompilerConfigExtra(
        cudagraphs=cudagraphs,
        graph_id=graph_id,
        forward_device=forward_device,
        cudagraphs_bwd_override=cudagraphs_bwd_override,
        forward_is_partitioned=forward_is_partitioned,
    )