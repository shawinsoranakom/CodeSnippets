def create_hop_fw_bw(
    fw_gm: GraphModule,
    *_args: Any,
) -> tuple[GraphModule, GraphModule, int, int, set[int]]:
    """
    Traces a joint, applies passes and partitions it
    """
    # Keeping these imports here
    # Avoid circular dependencies once we upstream with dynamo frontend
    from torch._dispatch.python import suspend_functionalization
    from torch._functorch.aot_autograd import AOTConfig, create_joint
    from torch._guards import detect_fake_mode
    from torch._subclasses.fake_tensor import FakeTensor, FakeTensorMode
    from torch._subclasses.functional_tensor import disable_functional_mode
    from torch.fx.experimental.proxy_tensor import disable_proxy_modes_tracing, make_fx

    local_map_kwargs = fw_gm.meta["local_map_kwargs"]  # type: ignore[attr-defined]
    if "in_placements" not in local_map_kwargs:
        raise AssertionError("'in_placements' not found in local_map_kwargs")
    if "out_placements" not in local_map_kwargs:
        raise AssertionError("'out_placements' not found in local_map_kwargs")
    if "device_mesh" not in local_map_kwargs:
        raise AssertionError("'device_mesh' not found in local_map_kwargs")
    if len(local_map_kwargs["in_placements"]) != len(_args):
        raise AssertionError(
            f"in_placements length ({len(local_map_kwargs['in_placements'])}) != _args length ({len(_args)})"
        )

    dummy_aot_config = AOTConfig(
        fw_compiler=None,  # type: ignore[arg-type]
        bw_compiler=None,  # type: ignore[arg-type]
        partition_fn=None,  # type: ignore[arg-type]
        decompositions={},
        num_params_buffers=0,
        aot_id=0,
        keep_inference_input_mutations=False,
    )

    with suspend_functionalization(), disable_functional_mode():
        with disable_proxy_modes_tracing():
            # If someone runs this hop under the default compiler backend ("eager")
            # Then this path will be run with the actual user inputs. We convert them
            # to fake tensors in order to not perform any actual compute.

            fake_mode = detect_fake_mode(_args)
            if fake_mode is None:
                fake_mode = FakeTensorMode(allow_non_fake_inputs=True)

            with fake_mode:
                fw_inputs = redistribute_fw_inputs(
                    _args,
                    local_map_kwargs["in_placements"],
                    local_map_kwargs["device_mesh"],
                )
                if len(fw_inputs) != len(local_map_kwargs["in_placements"]):
                    raise AssertionError(
                        f"fw_inputs length ({len(fw_inputs)}) != "
                        f"in_placements length ({len(local_map_kwargs['in_placements'])})"
                    )

            if not all(
                isinstance(t, (FakeTensor, int, torch.SymInt)) for t in fw_inputs
            ):
                raise AssertionError(f"Unexpected element in {fw_inputs=}")

            ctx = (
                fake_mode.shape_env.ignore_fresh_unbacked_symbols
                if fake_mode.shape_env is not None
                else contextlib.nullcontext
            )
            with ctx():
                fw_outs = fw_gm(*fw_inputs)

            example_grads = pytree.tree_map(
                _new_tensor,
                fw_outs,
            )
            if not isinstance(example_grads, (list, tuple)):
                example_grads = [example_grads]

            num_fw_inputs = len(fw_inputs)
            num_fw_outputs = len(example_grads)

        def joint_f(
            *primals_and_tangents: list[torch.Tensor],
        ) -> Any:
            primals = primals_and_tangents[:num_fw_inputs]
            tangents = primals_and_tangents[num_fw_inputs:]

            def prepare_fw_with_masks(
                fw_gm: torch.fx.GraphModule,
            ) -> Callable[..., Any]:
                def fw_with_masks(*args: Any) -> tuple[tuple[Any], list[bool]]:
                    # The Interpreter here is required to propagate metadata
                    # from the dynamo graph body to the local_map graph body.
                    # This is required for fx_traceback.annotate for work.
                    fw_out = torch.fx.Interpreter(fw_gm).run(*args)
                    if not isinstance(fw_out, tuple):
                        raise AssertionError(
                            "Dynamo traced submodule should return tuple"
                        )
                    return fw_out, [
                        bool(isinstance(ret, torch.Tensor) and ret.requires_grad)
                        for ret in fw_out
                    ]

                return fw_with_masks

            fw_outs, grads = create_joint(
                prepare_fw_with_masks(fw_gm), aot_config=dummy_aot_config
            )(primals, tangents)
            from torch.fx.experimental.symbolic_shapes import has_free_unbacked_symbols

            if has_free_unbacked_symbols((*fw_outs, *grads)):
                raise AssertionError(
                    "Unbacked symints leaking outside of the joint graph is not yet supported."
                )

            maybe_clone = clone_outputs_aliasing_inputs(primals_and_tangents)
            # put grads first to work with existing hop utils
            return pytree.tree_map(maybe_clone, (*grads, *fw_outs))

        filtered_grads_idx = set()
        for i, example_grad in enumerate(example_grads):
            # Filter out grads that are None or do not require_grad.
            # The AOTAutograd utils we rely on force this assumption.
            # We must also filter the runtime tangents too.
            if example_grad is not None and (
                isinstance(example_grad, torch.Tensor) and example_grad.requires_grad
            ):
                filtered_grads_idx.add(i)

        primals_and_tangents = [
            *fw_inputs,
            *[example_grads[i] for i in filtered_grads_idx],
        ]
        joint_hop_gm = make_fx(joint_f)(*primals_and_tangents)
        from torch._functorch._aot_autograd.graph_capture import (
            copy_fwd_metadata_to_bw_nodes,
        )

        copy_fwd_metadata_to_bw_nodes(joint_hop_gm)

        from torch._functorch._aot_autograd.graph_compile import prepare_for_partitioner
        from torch._inductor.compile_fx import partition_fn

        # Match partitioner convention
        prepped_joint_hop_gm = prepare_for_partitioner(
            joint_hop_gm, num_fw_inputs, num_fw_outputs
        )
        with disable_proxy_modes_tracing():
            # Also runs joint passes
            new_fw_gm, new_bw_gm = partition_fn(
                prepped_joint_hop_gm,
                [],
                num_fwd_outputs=num_fw_outputs,
                static_lifetime_input_indices=[],
            )

        # Fix tags because min-cut does not respect fw/bw boundary, breaking
        # default partitioner's assumptions.
        for node in new_fw_gm.graph.nodes:
            node.meta["partitioner_tag"] = "is_forward"
        for node in new_bw_gm.graph.nodes:
            node.meta["partitioner_tag"] = "is_backward"

        # Propagate meta onto fw/bw graphs, later will be set on proxied nodes
        new_fw_gm.meta["local_map_kwargs"] = local_map_kwargs
        new_bw_gm.meta["local_map_kwargs"] = {**local_map_kwargs}
        # Okay because Autoparallel assumes same sharding between param and grads
        new_bw_gm.meta["local_map_kwargs"]["in_placements"] = tuple(
            [local_map_kwargs["out_placements"][i] for i in filtered_grads_idx]
        )
        new_bw_gm.meta["local_map_kwargs"]["out_placements"] = local_map_kwargs[
            "in_placements"
        ]

        # Validate Forward
        fw_kwargs = new_fw_gm.meta["local_map_kwargs"]
        expected_fw_inputs = len(fw_kwargs["in_placements"])
        expected_fw_outputs = len(fw_kwargs["out_placements"])
        actual_fw_inputs = len(new_fw_gm.graph.find_nodes(op="placeholder"))
        actual_fw_outputs = num_fw_outputs
        if expected_fw_inputs != actual_fw_inputs:
            raise AssertionError(
                f"expected_fw_inputs ({expected_fw_inputs}) != actual_fw_inputs ({actual_fw_inputs})"
            )
        if expected_fw_outputs != actual_fw_outputs:
            raise AssertionError(
                f"expected_fw_outputs ({expected_fw_outputs}) != actual_fw_outputs ({actual_fw_outputs})"
            )

        # Validate Activations
        if len(new_fw_gm.graph.find_nodes(op="output")) != 1:
            raise AssertionError(
                f"Expected exactly 1 output node, got {len(new_fw_gm.graph.find_nodes(op='output'))}"
            )
        num_activations = (
            len(new_fw_gm.graph.find_nodes(op="output")[0].args[0]) - num_fw_outputs
        )
        # tensors first, then symints
        if num_activations < 0:
            raise AssertionError(f"num_activations must be >= 0, got {num_activations}")

        # Validate Backward
        bw_kwargs = new_bw_gm.meta["local_map_kwargs"]
        expected_bw_inputs = len(bw_kwargs["in_placements"])
        expected_bw_outputs = len(bw_kwargs["out_placements"])
        actual_bw_inputs = (
            len(new_bw_gm.graph.find_nodes(op="placeholder")) - num_activations
        )
        if actual_bw_inputs <= 0:
            raise AssertionError(
                f"actual_bw_inputs must be > 0, got {actual_bw_inputs}"
            )
        if expected_fw_inputs + expected_bw_inputs != len(primals_and_tangents):
            raise AssertionError(
                f"expected_fw_inputs ({expected_fw_inputs}) + expected_bw_inputs ({expected_bw_inputs}) "
                f"!= primals_and_tangents length ({len(primals_and_tangents)})"
            )
        if actual_fw_inputs + actual_bw_inputs != len(primals_and_tangents):
            raise AssertionError(
                f"actual_fw_inputs ({actual_fw_inputs}) + actual_bw_inputs ({actual_bw_inputs}) "
                f"!= primals_and_tangents length ({len(primals_and_tangents)})"
            )
        if len(new_bw_gm.graph.find_nodes(op="output")) != 1:
            raise AssertionError(
                f"Expected exactly 1 bw output node, got {len(new_bw_gm.graph.find_nodes(op='output'))}"
            )
        actual_bw_outputs = len(new_bw_gm.graph.find_nodes(op="output")[0].args[0])
        if expected_bw_inputs != actual_bw_inputs:
            raise AssertionError(
                f"expected_bw_inputs ({expected_bw_inputs}) != actual_bw_inputs ({actual_bw_inputs})"
            )
        if expected_bw_outputs != actual_bw_outputs:
            raise AssertionError(
                f"expected_bw_outputs ({expected_bw_outputs}) != actual_bw_outputs ({actual_bw_outputs})"
            )

        new_fw_gm.meta["num_activations"] = num_activations
        new_fw_gm.meta["is_backward"] = False
        new_bw_gm.meta["num_activations"] = num_activations
        new_bw_gm.meta["is_backward"] = True

        return new_fw_gm, new_bw_gm, num_fw_inputs, num_fw_outputs, filtered_grads_idx