def functionalize_rng_ops(
    joint_module: fx.GraphModule,
    fw_module: fx.GraphModule,
    bw_module: fx.GraphModule,
    num_sym_nodes: int,
) -> tuple[fx.GraphModule, fx.GraphModule]:
    # During user-driven activation checkpointing, we have to ensure that a rng
    # op in fwd yields the same output as the recomputed rng op in the bwd.  To
    # do this, we use functionalize wrappers to wrap the random ops and share
    # rng state between the fwd and bwd graphs.

    # There are 3 main steps to do this
    # Step 1 - Construct a mapping of rng node between the fwd and its counterpart in bwd.
    # Step 2 - Modify the fwd pass such that
    #   1) Replace rand with run_and_save_rng_state wrapper
    #   2) Replace the users of the original op with the output[1] of this op.
    #   3) Collect all the rng_state - output[0] of each op, and make them
    #   output nodes. Special care needs to be taken here because fwd outputs
    #   has symints at the very end.
    # Step 3 - Modify the bwd pass such that
    #   1) Add the input nodes just before the tangents for the stashed rng states
    #   2) Replace rand with run_with_save_rng_state wrappers
    #   3) Use the stashed states as inputs to these ops

    # Unique id to generate name
    uid = itertools.count()

    def get_rng_ops(gmod: fx.GraphModule) -> dict[str, fx.Node]:
        random_nodes: dict[str, fx.Node] = {}
        for node in gmod.graph.nodes:
            if (
                node.op == "call_function"
                and hasattr(node.target, "tags")
                and torch.Tag.nondeterministic_seeded in node.target.tags
            ):
                random_nodes[node.name] = node
        return random_nodes

    def get_device(node: fx.Node) -> torch.device | None:
        """
        Check the example value of the node outputs to find the device type.
        """
        if "val" not in node.meta:
            return None

        candidates = node.meta["val"]
        if not isinstance(candidates, tuple):
            candidates = (candidates,)

        for candidate in candidates:
            if isinstance(candidate, torch.Tensor):
                if candidate.device.type == "cuda":
                    return candidate.device

        return torch.device("cpu")

    def get_sample_rng_state(device: torch.device | None) -> torch.Tensor:
        from torch._guards import detect_fake_mode

        fake_mode = detect_fake_mode()
        if fake_mode is None:
            raise AssertionError("fake_mode must not be None")
        with fake_mode:
            if device is not None and device.type == "cuda":
                return fake_mode.from_tensor(torch.cuda.get_rng_state())
            return fake_mode.from_tensor(torch.get_rng_state())

    # Step 1 - Construct a mapping of rng node between the fwd and its counterpart in bwd.
    joint_graph_rng_ops = get_rng_ops(joint_module)
    fw_graph_rng_ops = get_rng_ops(fw_module)
    bw_graph_rng_ops = get_rng_ops(bw_module)
    recomputable_rng_ops_map = {}
    for node in joint_module.graph.nodes:
        if (
            must_recompute(node)
            and hasattr(node.target, "tags")
            and torch.Tag.nondeterministic_seeded in node.target.tags
        ):
            # Skip if the node doesn't exist in both forward and backward graphs.
            # This can happen when the RNG op's output is not needed for gradient
            # computation and gets eliminated by dead code elimination.
            if node.name not in fw_graph_rng_ops or node.name not in bw_graph_rng_ops:
                continue
            base_node = joint_graph_rng_ops[node.name]
            fw_node = fw_graph_rng_ops[node.name]
            bw_node = bw_graph_rng_ops[node.name]
            recomputable_rng_ops_map[base_node] = {"fwd": fw_node, "bwd": bw_node}

    run_and_save_rng = torch._prims.rng_prims.run_and_save_rng_state
    run_with_rng_state = torch._prims.rng_prims.run_with_rng_state

    bw_tangent_start_node = None
    for node in bw_module.graph.find_nodes(op="placeholder"):
        if "tangent" in node.name:
            bw_tangent_start_node = node
            break
    if bw_tangent_start_node is None:
        raise RuntimeError(
            "Couldn't find tangent node in graph inputs. This is unexpected, please file a bug if you see this"
        )

    fw_rng_state_outputs: list[fx.Node] = []

    last_fwd_input = next(reversed(fw_module.graph.find_nodes(op="placeholder")))
    last_bwd_input = next(reversed(bw_module.graph.find_nodes(op="placeholder")))

    devices = OrderedSet(
        get_device(node_pair["fwd"]) for node_pair in recomputable_rng_ops_map.values()
    )
    # pyrefly: ignore [unbound-name]
    devices.discard(torch.device("cpu"))
    # multiple cuda devices won't work with cudagraphs anyway,
    # fallback to non graphsafe rng checkpointing
    multi_cuda_devices = len(devices) > 1

    # this changes numerics, so if fallback_random is set we will not use it
    # pyrefly: ignore [unbound-name]
    ind_config = torch._inductor.config
    use_rng_graphsafe_rng_functionalization = (
        config.graphsafe_rng_functionalization
        and not multi_cuda_devices
        and (
            not ind_config.fallback_random
            or ind_config.test_configs.graphsafe_rng_func_ignores_fallback_random
        )
    )

    for rng_count, node_pair in enumerate(recomputable_rng_ops_map.values()):
        # Step 2 - Modify the fwd pass such that
        fw_node = node_pair["fwd"]
        bw_node = node_pair["bwd"]
        device = get_device(fw_node)

        fw_graph = fw_module.graph
        bw_graph = bw_module.graph

        if (
            use_rng_graphsafe_rng_functionalization
            and device is not None
            and device.type == "cuda"
        ):
            last_fwd_input, last_bwd_input = apply_graphsafe_rng_functionalization(
                fw_module,
                bw_module,
                fw_node,
                bw_node,
                device,
                rng_count,
                last_fwd_input,
                last_bwd_input,
            )
        else:
            with fw_graph.inserting_before(fw_node):
                functional_fw_node = fw_graph.create_node(
                    "call_function",
                    run_and_save_rng,
                    # pyrefly: ignore [bad-argument-type]
                    args=(
                        fw_node.target,
                        *fw_node.args,
                    ),  # pyrefly: ignore[bad-argument-type]
                    kwargs=fw_node.kwargs,
                )
                state = fw_graph.create_node(
                    "call_function",
                    operator.getitem,
                    args=(functional_fw_node, 0),
                    kwargs={},
                )
                state.meta["val"] = get_sample_rng_state(device)

                rng_output = fw_graph.create_node(
                    "call_function",
                    operator.getitem,
                    args=(
                        functional_fw_node,
                        1,
                    ),
                    kwargs={},
                )
                # Copy the meta data from the original node
                rng_output.meta = copy.copy(fw_node.meta)

                fw_node.replace_all_uses_with(rng_output)
                fw_graph.erase_node(fw_node)
                fw_rng_state_outputs.append(state)

            # Step 3 - Modify the bwd pass such that
            with bw_graph.inserting_before(bw_tangent_start_node):
                state_name = f"rng_state_output_{next(uid)}"
                bw_rng_state_node = bw_graph.placeholder(state_name)
                bw_rng_state_node.meta["val"] = get_sample_rng_state(device)

            with bw_graph.inserting_before(bw_node):
                rng_output = bw_graph.create_node(
                    "call_function",
                    run_with_rng_state,
                    # pyrefly: ignore [bad-argument-type]
                    args=(
                        bw_rng_state_node,
                        bw_node.target,
                        *bw_node.args,
                    ),  # pyrefly: ignore[bad-argument-type]
                    kwargs=bw_node.kwargs,
                )

                bw_node.replace_all_uses_with(rng_output)
                bw_graph.erase_node(bw_node)

    # Add the rng states in the output of the fwd graph. AOT Autograd assumes
    # that symints are at the end of forward graph outputs. So, insert the new
    # rng states accordingly.
    if fw_rng_state_outputs:
        fw_output_node = next(iter(fw_module.graph.find_nodes(op="output")))
        fw_outputs = fw_output_node.args[0]
        sym_node_start_idx = len(fw_outputs) - num_sym_nodes
        outputs = (
            fw_outputs[:sym_node_start_idx]
            + tuple(fw_rng_state_outputs)
            + fw_outputs[sym_node_start_idx:]
        )
        fw_module.graph.output(outputs)
        fw_module.graph.erase_node(fw_output_node)
    fw_module.recompile()
    bw_module.recompile()
    return fw_module, bw_module