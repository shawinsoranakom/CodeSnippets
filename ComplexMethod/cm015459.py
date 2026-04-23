def _test_shard_placement_fn_tp_ep(
        self, tp_degree, dp_replicate, reshard_non_layer_modules
    ):
        ep_degree = 2
        result = self._init_parallel_meshes(tp_degree, dp_replicate, ep_degree)
        if result is None:
            return
        (
            tp_mesh,
            dp_mesh,
            ep_mesh,
            efsdp_mesh,
            dp_mesh_info,
            efsdp_mesh_info,
        ) = result
        # reshard_root as int must be a factor of every group's
        # shard mesh size; skip configs where it is not.
        if isinstance(reshard_non_layer_modules, int) and not isinstance(
            reshard_non_layer_modules, bool
        ):
            for mi in (dp_mesh_info, efsdp_mesh_info):
                if mi.shard_mesh_size % reshard_non_layer_modules != 0:
                    return
        model_args = ModelArgs(
            n_layers=2,
            vocab_size=256,
            max_seq_len=32,
            dim=64,
            n_heads=4,
            dropout_p=0.0,
            num_experts=8,
        )
        torch.manual_seed(42)
        model = Transformer(model_args)
        ref_model = copy.deepcopy(model).to(device_type)
        Transformer.parallelize(
            model, tp_mesh=tp_mesh, use_seq_parallel=False, ep_mesh=ep_mesh
        )
        for block in model.layers:
            expert_params = set(block.expert_layer.experts.parameters())

            def _shard_placement_fn(
                param,
                _expert_params=expert_params,
            ):
                if param in _expert_params:
                    return ShardPlacementResult(
                        placement=Shard(0),
                        mesh_info=efsdp_mesh_info,
                    )
                return ShardPlacementResult(
                    placement=Shard(0),
                    mesh_info=dp_mesh_info,
                )

            # Blocks always have DTensor expert params (from EP), so int
            # reshard is not supported; do not pass reshard_after_forward.
            fully_shard(
                block,
                mesh=dp_mesh,
                shard_placement_fn=_shard_placement_fn,
            )
        # Group tok_embeddings, norm, and output together since
        # output.weight is tied to tok_embeddings.weight
        # These modules have no DTensor params when tp_degree == 1.
        # With TP, root params are DTensors and int reshard is unsupported.
        if tp_mesh is not None:
            reshard_non_layer_modules = True
        fully_shard(
            [model.tok_embeddings, model.norm, model.output],
            mesh=dp_mesh,
            reshard_after_forward=reshard_non_layer_modules,
        )
        fully_shard(
            model, mesh=dp_mesh, reshard_after_forward=reshard_non_layer_modules
        )
        for (name, param), (_, ref_param) in zip(
            model.named_parameters(), ref_model.named_parameters()
        ):
            full_param = param.full_tensor()
            self.assertEqual(full_param, ref_param)
        ref_expert_params = {
            p for b in ref_model.layers for p in b.expert_layer.experts.parameters()
        }
        optim = torch.optim.Adam(model.parameters(), lr=1e-2)
        ref_optim = torch.optim.Adam(ref_model.parameters(), lr=1e-2)
        torch.manual_seed(42 + self.rank // tp_degree)
        inp = torch.randint(
            0,
            model_args.vocab_size,
            (2, model_args.max_seq_len),
            device=device_type.type,
        )
        dp_replicate_group = (
            dp_mesh["dp_replicate"].get_group() if dp_replicate > 1 else None
        )
        for iter_idx in range(5):
            ref_loss = ref_model(inp).sum()
            loss = model(inp).sum()
            ref_loss.backward()
            loss.backward()
            for param in ref_model.parameters():
                if param.grad is None:
                    continue
                if param in ref_expert_params:
                    dist.all_reduce(
                        param.grad, op=dist.ReduceOp.SUM, group=ep_mesh.get_group()
                    )
                    dist.all_reduce(
                        param.grad, op=dist.ReduceOp.AVG, group=efsdp_mesh.get_group()
                    )
                    if dp_replicate_group is not None:
                        dist.all_reduce(
                            param.grad,
                            op=dist.ReduceOp.AVG,
                            group=dp_replicate_group,
                        )
                else:
                    dist.all_reduce(param.grad, op=dist.ReduceOp.AVG)
            ref_optim.step()
            optim.step()
            ref_optim.zero_grad(set_to_none=(iter_idx % 2 == 0))
            optim.zero_grad(set_to_none=(iter_idx % 2 == 0))
            self.assertEqual(ref_loss, loss)