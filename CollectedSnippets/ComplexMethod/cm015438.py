def _test_train_shared_params(
        self,
        use_activation_checkpointing: bool,
    ):
        torch.manual_seed(42)
        model_args = ModelArgs(n_layers=3, dropout_p=0.0, weight_tying=True)
        model = Transformer(model_args)
        ref_model = copy.deepcopy(model).to(device_type)

        ref_optim = torch.optim.Adam(ref_model.parameters(), lr=1e-2)
        for module in model.modules():
            if isinstance(module, TransformerBlock):
                if use_activation_checkpointing:
                    checkpoint(module)
                replicate(module)
        replicate(model)
        optim = torch.optim.Adam(model.parameters(), lr=1e-2)

        torch.manual_seed(42 + self.rank + 1)
        for iter_idx in range(10):
            inp = torch.randint(
                0, model_args.vocab_size, (2, 16), device=device_type.type
            )
            losses: list[torch.Tensor] = []
            for _model in (ref_model, model):
                losses.append(_model(inp).sum())
                losses[-1].backward()

            for param in ref_model.parameters():
                if param.grad is not None:
                    dist.all_reduce(param.grad)
                    param.grad.div_(self.world_size)

            for _optim in (ref_optim, optim):
                _optim.zero_grad(set_to_none=(iter_idx % 2 == 0))
                _optim.step()

            self.assertEqual(losses[0], losses[1])