def test_to_float64_after_init(self):
        """Tests that the user can cast the module to float64 after init."""
        # NOTE: Test fp64 instead of a lower precision dtype like bf16 for
        # better numerics. The important part is changing the dtype.

        torch.manual_seed(42)
        mlp_dim, device, dtype = 4, device_type, torch.float64
        model = MLP(mlp_dim, device=device)
        for param in model.parameters():
            dist.broadcast(param, src=0)
        ref_model = copy.deepcopy(model).to(dtype)

        ref_optim = torch.optim.Adam(ref_model.parameters(), lr=1e-2)
        for module in (model.in_proj, model.out_proj, model):
            replicate(module)
        model.to(dtype)
        for param in model.parameters():
            self.assertEqual(param.dtype, dtype)
            self.assertEqual(param.to_local().dtype, dtype)
            self.assertEqual(param._spec.tensor_meta.dtype, dtype)
        optim = torch.optim.Adam(model.parameters(), lr=1e-2, foreach=True)
        check_sharded_parity(self, ref_model, model)
        torch.manual_seed(42 + self.rank + 1)
        inp = torch.randn((2, mlp_dim), device=device_type.type, dtype=dtype)
        for iter_idx in range(10):
            losses: list[torch.Tensor] = []
            for _model in (ref_model, model):
                losses.append(_model(inp).sum())
                losses[-1].backward()

            for param in ref_model.parameters():
                if param.grad is not None:
                    dist.all_reduce(param.grad)
                    param.grad.div_(self.world_size)

            self.assertEqual(losses[0], losses[1])
            check_sharded_parity(self, ref_model, model)
            for param in model.parameters():
                self.assertEqual(param.dtype, dtype)
                self.assertEqual(param.to_local().dtype, dtype)
                self.assertEqual(param._spec.tensor_meta.dtype, dtype)
                self.assertEqual(param.grad.dtype, dtype)
                self.assertEqual(param.grad.to_local().dtype, dtype)
                self.assertEqual(param.grad._spec.tensor_meta.dtype, dtype)
            for _optim in (ref_optim, optim):
                _optim.step()
                _optim.zero_grad(set_to_none=(iter_idx % 2 == 0))