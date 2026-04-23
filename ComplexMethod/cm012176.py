def _run_pre_dispatch_passes(
    gm: torch.fx.GraphModule,
    example_inputs: Sequence[object] = (),
    add_passes: str | None = None,
    remove_passes: str | None = None,
) -> None:
    # order matters
    default_pass_list = [
        # normalize passes, must be called as the first passes
        normalization_pass_aten,
        normalize_node_kwargs_pass,
        remove_noop_pass,
        relu_nan_to_num,
        fuse_chunk_reshape_concat_pass,
        group_batch_fusion_passes,
        normalize_node_kwargs_pass,
        fuse_chunk_squeeze_cat_pass,
        merge_concats_pass,
        fuse_split_linear_add_pass,
        remove_reshape_pass,
        fuse_parallel_linear_pass,
        remove_split_ops_pass,
        stack_to_unsqueeze_pass,  # run before fuse_chunk_reshape_unsqueeze_concat_pass
        fuse_chunk_reshape_unsqueeze_concat_pass,
    ]

    full_pass_list = default_pass_list + [
        fuse_split_getitem_squeeze_cat,
        use_triton_dot_compress,
        use_triton_lce_replace_simple_LCE,
        use_triton_lce_replace_normal_LCE,
        use_matmul_fuse_lce_replace_first_LCE,
        use_matmul_lce_replace_normal_LCE,
    ]

    log.info(
        f"pre_grad_passes: add_passes: {add_passes}, remove_pass: {remove_passes}"  # noqa: G004
    )
    add_passes_list = []
    remove_passes_list = []
    if add_passes:
        add_passes_list = add_passes.split(",")
    if remove_passes:
        remove_passes_list = remove_passes.split(",")

    shape_prop = lambda mod: ShapeProp(  # noqa: E731
        gm=mod,
        # pyre-fixme[16]: Module `torch._dynamo.utils` has no attribute `detect_fake_mode`
        fake_mode=detect_fake_mode(example_inputs),
    ).propagate(*tuple(example_inputs))

    for p in default_pass_list:
        pass_name, pass_func = _get_pass_name_func(p)
        # should not happen
        if pass_name is None or pass_func is None:
            continue
        if pass_name in remove_passes_list:
            continue
        pass_execution_and_save(
            pass_func,
            gm,
            example_inputs,
            f"[Pre grad(predispatch IR)] Apply {pass_name} pass",
        )

    for p in full_pass_list:
        pass_name, pass_func = _get_pass_name_func(p)
        if pass_name is None or pass_func is None:
            continue
        if pass_name in add_passes_list:
            pass_execution_and_save(
                pass_func,
                gm,
                example_inputs,
                f"[Pre grad(predispatch IR)] Apply {pass_name} pass",
            )

    if "remove_noop" not in remove_passes_list:
        # Remove noops at the end, which may be generated other passes.
        pass_execution_and_save(
            remove_noop_pass,
            gm,
            example_inputs,
            "[Pre grad(predispatch IR)]Apply remove_noop pass",
        )
    shape_prop(gm)