def test_explicit_prefetching(self):
        torch.manual_seed(42)
        model_args = ModelArgs(n_layers=8, dropout_p=0.0)
        model = Transformer(model_args)
        ref_model = replicate(copy.deepcopy(model).to(device_type))
        ref_optim = torch.optim.AdamW(ref_model.parameters(), lr=1e-2)
        for layer in itertools.chain(model.layers, [model]):
            fully_shard(layer)
        optim = torch.optim.AdamW(model.parameters(), lr=1e-2)

        num_to_forward_prefetch = num_to_backward_prefetch = 2
        for i, layer in enumerate(model.layers):
            if i >= len(model.layers) - num_to_forward_prefetch:
                break
            layers_to_prefetch = [
                model.layers[i + j] for j in range(1, num_to_forward_prefetch + 1)
            ]
            layer.set_modules_to_forward_prefetch(layers_to_prefetch)
        for i, layer in enumerate(model.layers):
            if i < num_to_backward_prefetch:
                continue
            layers_to_prefetch = [
                model.layers[i - j] for j in range(1, num_to_backward_prefetch + 1)
            ]
            layer.set_modules_to_backward_prefetch(layers_to_prefetch)

        torch.manual_seed(42 + self.rank)
        inp = torch.randint(0, model_args.vocab_size, (2, 8), device=device_type.type)
        for _ in range(10):
            losses: list[torch.Tensor] = []
            for _model, _optim in ((ref_model, ref_optim), (model, optim)):
                _optim.zero_grad()
                losses.append(_model(inp).sum())
                losses[-1].backward()
                _optim.step()
            self.assertEqual(losses[0], losses[1])