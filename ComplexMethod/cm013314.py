def parallelize(
        module: "Transformer",
        tp_mesh: DeviceMesh | None,
        use_seq_parallel: bool,
        local_output_for_attn: bool = False,
        ep_mesh: DeviceMesh | None = None,
    ) -> nn.Module:
        if not isinstance(module, Transformer):
            raise AssertionError(f"Requires Transformer but got {module}")
        if tp_mesh is None and ep_mesh is None:
            raise ValueError("At least one of tp_mesh or ep_mesh must be provided")

        # Parallelize the root submodules with TP.
        if tp_mesh is not None:
            if use_seq_parallel:
                root_plan = {
                    "tok_embeddings": RowwiseParallel(
                        input_layouts=Replicate(), output_layouts=Shard(1)
                    ),
                    "pos_embeddings": RowwiseParallel(
                        input_layouts=Replicate(), output_layouts=Shard(0)
                    ),
                    "norm": SequenceParallel(),
                }
            else:
                root_plan = {
                    "tok_embeddings": RowwiseParallel(
                        input_layouts=Replicate(), output_layouts=Replicate()
                    ),
                    "pos_embeddings": RowwiseParallel(
                        input_layouts=Replicate(), output_layouts=Replicate()
                    ),
                }
            parallelize_module(module, tp_mesh, root_plan)

        # Parallelize the attention and feed forward submodules.
        for layer in module.layers:
            if tp_mesh is not None:
                layer_parallelize_plan = {}
                if use_seq_parallel:
                    layer_parallelize_plan["attention"] = PrepareModuleInput(
                        input_layouts=Shard(1),
                        desired_input_layouts=Replicate(),
                    )
                    # shard the RMSNorms
                    layer_parallelize_plan["attention_norm"] = SequenceParallel()
                    layer_parallelize_plan["ffn_norm"] = SequenceParallel()
                layer_parallelize_plan["attention.wq"] = ColwiseParallel(
                    use_local_output=local_output_for_attn
                )
                layer_parallelize_plan["attention.wk"] = ColwiseParallel(
                    use_local_output=local_output_for_attn
                )
                layer_parallelize_plan["attention.wv"] = ColwiseParallel(
                    use_local_output=local_output_for_attn
                )
                layer_parallelize_plan["attention.wo"] = (
                    RowwiseParallel(output_layouts=Shard(1))
                    if use_seq_parallel
                    else RowwiseParallel()
                )

                if not layer.has_experts:
                    layer_parallelize_plan["feed_forward.w1"] = (
                        ColwiseParallel(input_layouts=Shard(1))
                        if use_seq_parallel
                        else ColwiseParallel()
                    )
                    layer_parallelize_plan["feed_forward.w2"] = (
                        RowwiseParallel(output_layouts=Shard(1))
                        if use_seq_parallel
                        else RowwiseParallel()
                    )
                elif ep_mesh is None:
                    # No EP mesh provided, use TP for experts
                    layer_parallelize_plan["expert_layer.experts"] = (
                        TensorParallelForExpert(
                            input_layouts=Shard(0),
                            output_layouts=Shard(0),
                        )
                        if use_seq_parallel
                        else TensorParallelForExpert()
                    )

                parallelize_module(layer, tp_mesh, layer_parallelize_plan)

            # EP (+ optional TP) for experts
            if ep_mesh is not None and layer.has_experts:
                if tp_mesh is not None:
                    parallelize_module(
                        layer.expert_layer,
                        ep_mesh,
                        ExpertParallelWithTP(ep_mesh, tp_mesh),
                    )
                else:
                    parallelize_module(
                        layer.expert_layer.experts, ep_mesh, ExpertParallel()
                    )

        if tp_mesh is not None:
            # Parallelize the output submodule. If weight tying is enabled,
            # we need to make sure output.weight is sharded consistently as
            # tok_embeddings.weight, at the cost of the all_reduce operation
            # using RowwiseParallel.
            output_parallelize_plan = (
                ColwiseParallel(
                    input_layouts=Shard(1),
                    output_layouts=Replicate(),
                )
                if use_seq_parallel
                else ColwiseParallel(output_layouts=Replicate())
            )
            parallelize_module(module.output, tp_mesh, output_parallelize_plan)

            if local_output_for_attn:
                for layer in module.layers:
                    layer.attention.n_heads = (
                        module.model_args.n_heads // tp_mesh.size()
                    )

            # Manually set output.weight so that parameters and gradients
            # are shared.
            if module.model_args.weight_tying:
                module.output.weight = module.tok_embeddings.weight

        return module