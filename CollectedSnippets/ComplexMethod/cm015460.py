def _test_train_parity_hsdp(
        self,
        global_mesh: DeviceMesh,
        reshard_after_forward: bool,
        use_activation_checkpointing: bool,
        mlp_dim: int,
        sync_gradients_at_last_batch: bool,
        offload_policy: CPUOffloadPolicy,
    ):
        # pin_memory requires an accelerator, skip on CPU
        if device_type.type == "cpu" and offload_policy.pin_memory:
            return
        torch.manual_seed(42)
        model = nn.Sequential(
            nn.LayerNorm(mlp_dim, bias=False),
            MLP(mlp_dim, dim_multiplier=3),
            MLP(mlp_dim),
            MLP(mlp_dim, dim_multiplier=3),
        )
        ref_model = copy.deepcopy(model).to(device_type)
        replicate(
            ref_model,
            device_ids=_get_device_ids(self.rank),
        )
        ref_optim = torch.optim.Adam(ref_model.parameters(), lr=1e-2)
        for mlp in model:
            if use_activation_checkpointing:
                checkpoint(mlp)
            fully_shard(
                mlp,
                mesh=global_mesh,
                reshard_after_forward=reshard_after_forward,
                offload_policy=offload_policy,
            )
        fully_shard(
            model,
            mesh=global_mesh,
            reshard_after_forward=reshard_after_forward,
            offload_policy=offload_policy,
        )
        optim = torch.optim.Adam(model.parameters(), lr=1e-2)
        check_sharded_parity(self, ref_model, model)
        torch.manual_seed(42 + self.rank + 1)
        device = device_type
        num_microbatches = 3
        for iter_idx in range(5):
            for microbatch_idx in range(num_microbatches):
                is_last_microbatch = microbatch_idx == num_microbatches - 1
                if sync_gradients_at_last_batch:
                    model.set_requires_gradient_sync(is_last_microbatch)
                inp = torch.randn((8, mlp_dim), device=device)
                losses: list[torch.Tensor] = []
                for _model, _optim in ((ref_model, ref_optim), (model, optim)):
                    losses.append(_model(inp).sum())
                    losses[-1].backward()
                self.assertEqual(losses[0], losses[1])
            check_sharded_parity(self, ref_model, model)
            for _model, _optim in ((ref_model, ref_optim), (model, optim)):
                _optim.step()
                _optim.zero_grad(set_to_none=(iter_idx % 2 == 0))
            check_sharded_parity(self, ref_model, model)