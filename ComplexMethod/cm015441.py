def _test_replicate_tp(
        self,
        global_mesh: DeviceMesh,
        use_activation_checkpointing: bool,
        mlp_dim: int,
        foreach: bool,
    ):
        dp_mesh, tp_mesh = global_mesh["dp_replicate"], global_mesh["tp"]
        dp_pg = dp_mesh._flatten().get_group()  # used for `replicate()`

        torch.manual_seed(42)
        model = MLPStack(mlp_dim)
        ref_model = copy.deepcopy(model).to(device_type)

        ref_optim = torch.optim.Adam(ref_model.parameters(), lr=1e-2, foreach=foreach)

        parallelize_plan = {
            # Pass `use_local_output=False` to keep as DTensor to preserve
            # uneven activation dims
            "0.in_proj": ColwiseParallel(use_local_output=False),
            "0.out_proj": RowwiseParallel(use_local_output=False),
            "1.in_proj": ColwiseParallel(use_local_output=False),
            "1.out_proj": RowwiseParallel(use_local_output=False),
            "2.in_proj": ColwiseParallel(use_local_output=False),
            "2.out_proj": (RowwiseParallel()),
        }

        model = parallelize_module(model, tp_mesh, parallelize_plan)

        for module in model:
            if isinstance(module, nn.LayerNorm):
                continue
            if use_activation_checkpointing:
                checkpoint(module)
            replicate(module, mesh=dp_mesh)
        replicate(model, mesh=dp_mesh)

        # Checking parameters match orig model is critical to validate .full_tensor correctly replicates the
        # strided-sharded layers.
        for ref_p, p in zip(ref_model.parameters(), model.parameters()):
            self.assertIsInstance(p, DTensor)
            self.assertEqual(ref_p, p.full_tensor())

        optim = torch.optim.Adam(model.parameters(), lr=1e-2, foreach=foreach)

        torch.manual_seed(42 + dp_pg.rank() + 1)
        device = device_type
        for iter_idx in range(10):
            inp = torch.randn((8, mlp_dim), device=device)
            losses: list[torch.Tensor] = []
            for _model in (ref_model, model):
                losses.append(_model(inp).sum())
                losses[-1].backward()

            for param in ref_model.parameters():
                if param.grad is not None:
                    dist.all_reduce(param.grad, op=dist.ReduceOp.AVG)

            for _optim in (ref_optim, optim):
                _optim.zero_grad(set_to_none=(iter_idx % 2 == 0))
                _optim.step()
            self.assertEqual(losses[0], losses[1])
            check_sharded_parity(self, ref_model, model)

        for _, p in model.named_parameters():
            self.assertIsInstance(p, DTensor)
            self.assertEqual(p.device_mesh.ndim, 2)
            self.assertEqual(len(p.placements), 2)
            self.assertEqual(p.device_mesh.mesh_dim_names, ("dp_replicate", "tp"))