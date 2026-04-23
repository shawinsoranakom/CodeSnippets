def create_hop_joint_graph(
    fw_fn: Callable,
    fw_args: tuple[torch.Tensor | torch.SymInt, ...],
    functionalize: bool,
) -> HopJointGraph:
    fw_gm = materialize_as_graph(fw_fn, fw_args, force_enable_grad=True)
    fw_gm_output_nodes = _find_hop_subgraph_outputs(fw_gm)

    if not all(
        isinstance(n, torch.fx.Node) and "val" in n.meta for n in fw_gm_output_nodes
    ):
        raise AssertionError(
            "all fw_gm output nodes must be torch.fx.Node with 'val' in meta"
        )
    fw_gm_output_vals = tuple(n.meta["val"] for n in fw_gm_output_nodes)  # type: ignore[arg-type]

    if not all(isinstance(val, torch.Tensor) for val in fw_gm_output_vals):
        raise AssertionError(
            f"all fw_gm output values must be torch.Tensor, got {[type(v) for v in fw_gm_output_vals]}"
        )
    example_grads = tuple(torch.zeros_like(val) for val in fw_gm_output_vals)

    joint_fn = create_bw_fn(fw_fn, fw_args, return_fw_outputs=True)
    joint_gm = materialize_as_graph(
        joint_fn, fw_args + example_grads, force_enable_grad=True
    )
    if functionalize:
        # Need to first trace out the joint_fn with autograd info on
        # then functionalize the graph otherwise the grad information is lost
        joint_gm = materialize_as_graph(
            # pyrefly: ignore [bad-argument-type]
            torch.func.functionalize(joint_gm, remove="mutations_and_views"),
            fw_args + example_grads,
        )

    return HopJointGraph(
        joint_gm,
        len(fw_args),
        len(fw_gm_output_nodes),
        functionalized=functionalize,
    )