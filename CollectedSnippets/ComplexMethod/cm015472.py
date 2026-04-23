def _test_set_reduce_scatter_divide_factor(
        self, divide_factor: float, mesh_shape: tuple[int] | tuple[int, int]
    ):
        torch.manual_seed(42)
        model_args = ModelArgs(dropout_p=0.0, weight_tying=False)
        model = Transformer(model_args)
        ref_model = copy.deepcopy(model).to(device_type)
        ref_optim = torch.optim.AdamW(ref_model.parameters(), lr=1e-2)
        mesh_dim_names = ("outer",) if len(mesh_shape) == 1 else ("outer", "inner")
        mesh = init_device_mesh(
            device_type.type, mesh_shape, mesh_dim_names=mesh_dim_names
        )
        for module in model.modules():
            if isinstance(module, TransformerBlock):
                fully_shard(module, reshard_after_forward=False, mesh=mesh)
        model = fully_shard(model, reshard_after_forward=False, mesh=mesh)
        optim = torch.optim.AdamW(model.parameters(), lr=1e-2)
        model.set_gradient_divide_factor(divide_factor)

        # Get ref_model params which should have the specific division factor applied
        block_params = set()
        for ref_mod in ref_model.modules():
            if isinstance(ref_mod, TransformerBlock):
                block_params.update(ref_mod.parameters())
        non_block_params = set(ref_model.parameters()) - block_params

        torch.manual_seed(42 + self.rank)
        inp = torch.randint(0, model_args.vocab_size, (2, 16), device=device_type.type)

        for _ in range(10):
            ref_loss = ref_model(inp).sum()
            ref_loss.backward()
            for param in ref_model.parameters():
                factor = divide_factor if param in non_block_params else self.world_size
                param.grad.mul_(1.0 / factor)
                dist.all_reduce(param.grad)
            loss = model(inp).sum()
            loss.backward()
            ref_optim.step()
            optim.step()
            self.assertEqual(ref_loss, loss)
            # Check parity before calling zero_grad so that grads are also checked
            check_sharded_parity(self, ref_model, model)
            ref_optim.zero_grad()
            optim.zero_grad()