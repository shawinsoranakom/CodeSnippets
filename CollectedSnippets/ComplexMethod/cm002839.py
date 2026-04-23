def _init_weights(self, module: nn.Module):
        """Initialize the weights."""
        if isinstance(module, RwkvSelfAttention):
            layer_id = module.layer_id
            num_hidden_layers = module.config.num_hidden_layers
            hidden_size = module.config.hidden_size
            attention_hidden_size = module.attention_hidden_size

            ratio_0_to_1 = layer_id / (num_hidden_layers - 1)  # 0 to 1
            ratio_1_to_almost0 = 1.0 - (layer_id / num_hidden_layers)  # 1 to ~0

            time_weight = torch.tensor(
                [i / hidden_size for i in range(hidden_size)],
                dtype=module.time_mix_key.dtype,
                device=module.time_mix_key.device,
            )
            time_weight = time_weight[None, None, :]

            decay_speed = [
                -5 + 8 * (h / (attention_hidden_size - 1)) ** (0.7 + 1.3 * ratio_0_to_1)
                for h in range(attention_hidden_size)
            ]
            decay_speed = torch.tensor(decay_speed, dtype=module.time_decay.dtype, device=module.time_decay.device)
            zigzag = (
                torch.tensor(
                    [(i + 1) % 3 - 1 for i in range(attention_hidden_size)],
                    dtype=module.time_first.dtype,
                    device=module.time_first.device,
                )
                * 0.5
            )

            init.copy_(module.time_decay, decay_speed)
            init.copy_(module.time_first, torch.ones_like(module.time_first * math.log(0.3) + zigzag))

            init.copy_(module.time_mix_key, torch.pow(time_weight, ratio_1_to_almost0))
            init.copy_(module.time_mix_value, torch.pow(time_weight, ratio_1_to_almost0) + 0.3 * ratio_0_to_1)
            init.copy_(module.time_mix_receptance, torch.pow(time_weight, 0.5 * ratio_1_to_almost0))
        elif isinstance(module, RwkvFeedForward):
            layer_id = module.layer_id
            num_hidden_layers = module.config.num_hidden_layers
            hidden_size = module.config.hidden_size

            ratio_1_to_almost0 = 1.0 - (layer_id / num_hidden_layers)  # 1 to ~0

            time_weight = torch.tensor(
                [i / hidden_size for i in range(hidden_size)],
                dtype=module.time_mix_key.dtype,
                device=module.time_mix_key.device,
            )
            time_weight = time_weight[None, None, :]

            init.copy_(module.time_mix_key, torch.pow(time_weight, ratio_1_to_almost0))
            init.copy_(module.time_mix_receptance, torch.pow(time_weight, ratio_1_to_almost0))
        elif isinstance(module, nn.Linear):
            shape = module.weight.shape
            gain = 1.0
            scale = 1.0  # extra scale for gain
            if module.bias is not None:
                init.zeros_(module.bias)
            if shape[0] > shape[1]:
                gain = math.sqrt(shape[0] / shape[1])
            if shape[0] == self.config.vocab_size and shape[1] == self.config.hidden_size:  # final projection?
                scale = 0.5

            gain *= scale
            init.orthogonal_(module.weight, gain=gain)
        elif isinstance(module, nn.Embedding):
            shape = module.weight.shape
            gain = 1e-4 * math.sqrt(max(shape[0], shape[1]))
            init.orthogonal_(module.weight, gain=gain)
        elif isinstance(module, nn.LayerNorm):
            init.ones_(module.weight)
            init.zeros_(module.bias)