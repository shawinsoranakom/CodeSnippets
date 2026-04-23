def _test_train_parity_2d_transformer(self, use_shard_placement_fn: bool):
        torch.manual_seed(42)
        model_args = ModelArgs(n_layers=3, dropout_p=0.0)
        model = Transformer(model_args)
        ref_model = copy.deepcopy(model).to(device_type)
        ref_optim = torch.optim.AdamW(ref_model.parameters(), lr=1e-2)

        dp_size, tp_size = self.world_size // 2, 2
        global_mesh = init_device_mesh(
            device_type, (dp_size, tp_size), mesh_dim_names=("dp", "tp")
        )
        model = Transformer.parallelize(model, global_mesh["tp"], use_seq_parallel=True)

        def _shard_placement_fn(param: nn.Parameter) -> Shard | None:
            if isinstance(param, DTensor):
                for placement in param.placements:
                    if isinstance(placement, Shard):
                        shard_dim = param.ndim - 1 - placement.dim
                        if not (shard_dim >= 0):
                            raise AssertionError(
                                f"Expected shard_dim >= 0, got {shard_dim} for {param.shape}"
                            )
                        return Shard(shard_dim)
            return Shard(0)

        shard_placement_fn = _shard_placement_fn if use_shard_placement_fn else None
        for layer in model.layers:
            fully_shard(
                layer, mesh=global_mesh["dp"], shard_placement_fn=shard_placement_fn
            )
        fully_shard(
            model, mesh=global_mesh["dp"], shard_placement_fn=shard_placement_fn
        )
        optim = torch.optim.AdamW(model.parameters(), lr=1e-2)

        for param, ref_param in zip(model.parameters(), ref_model.parameters()):
            full_param = param.full_tensor()
            self.assertEqual(full_param, ref_param)

        torch.manual_seed(42 + global_mesh.get_local_rank("dp"))
        inp = torch.randint(0, model_args.vocab_size, (2, 16), device=device_type)
        for _ in range(5):
            ref_loss = ref_model(inp).sum()
            loss = model(inp).sum()
            self.assertEqual(ref_loss, loss)
            ref_loss.backward()
            loss.backward()
            for param in ref_model.parameters():
                if param.grad is not None:
                    dist.all_reduce(
                        param.grad,
                        group=global_mesh.get_group("dp"),
                        op=dist.ReduceOp.AVG,
                    )

            # Specially check the TP placement for `pos_embeddings.weight` and
            # its which since the grad naturally has replicate placement,
            # requiring FSDP to redistribute it to shard placement before FSDP
            # runs its reduce-scatter
            self.assertIsInstance(model.pos_embeddings.weight.placements[1], Shard)
            self.assertIsInstance(model.pos_embeddings.weight.grad.placements[1], Shard)
            for ref_param, param in zip(ref_model.parameters(), model.parameters()):
                full_grad = param.grad.full_tensor()
                self.assertEqual(ref_param.grad, full_grad)

            ref_optim.step()
            optim.step()
            ref_optim.zero_grad()
            optim.zero_grad()

        for param, ref_param in zip(model.parameters(), ref_model.parameters()):
            full_param = param.full_tensor()
            self.assertEqual(full_param, ref_param)