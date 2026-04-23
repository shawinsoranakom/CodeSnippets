def _init_weights(self, module: nn.Module):
        xavier_std = self.config.init_xavier_std
        std = self.config.init_std
        if isinstance(module, OneFormerTransformerModule):
            if module.input_projections is not None:
                for input_projection in module.input_projections:
                    if not isinstance(input_projection, nn.Sequential):
                        init.xavier_uniform_(input_projection.weight, gain=xavier_std)
                        init.constant_(input_projection.bias, 0)
        elif isinstance(module, OneFormerTransformerDecoder):
            init.xavier_uniform_(module.query_input_projection.weight, gain=xavier_std)
            init.constant_(module.query_input_projection.bias, 0)
        elif isinstance(module, OneFormerPixelDecoderEncoderMultiscaleDeformableAttention):
            init.constant_(module.sampling_offsets.weight, 0.0)
            thetas = torch.arange(module.n_heads, dtype=torch.int64).float() * (2.0 * math.pi / module.n_heads)
            grid_init = torch.stack([thetas.cos(), thetas.sin()], -1)
            grid_init = (
                (grid_init / grid_init.abs().max(-1, keepdim=True)[0])
                .view(module.n_heads, 1, 1, 2)
                .repeat(1, module.n_levels, module.n_points, 1)
            )
            for i in range(module.n_points):
                grid_init[:, :, i, :] *= i + 1

            init.copy_(module.sampling_offsets.bias, grid_init.view(-1))
            init.constant_(module.attention_weights.weight, 0.0)
            init.constant_(module.attention_weights.bias, 0.0)
            init.xavier_uniform_(module.value_proj.weight)
            init.constant_(module.value_proj.bias, 0.0)
            init.xavier_uniform_(module.output_proj.weight)
            init.constant_(module.output_proj.bias, 0.0)
        elif isinstance(module, OneFormerPixelDecoder):
            init.normal_(module.level_embed, std=0)
        elif isinstance(module, (OneFormerTransformerDecoderLayer, OneFormerTransformerDecoderQueryTransformer)):
            for p in module.parameters():
                if p.dim() > 1:
                    init.xavier_uniform_(p, gain=xavier_std)
        elif isinstance(module, OneFormerTextTransformer):
            proj_std = (module.width**-0.5) * ((2 * module.num_layers) ** -0.5)
            attn_std = module.width**-0.5
            fc_std = (2 * module.width) ** -0.5
            for layer in module.layers:
                init.normal_(layer.self_attn.in_proj_weight, std=attn_std)
                init.normal_(layer.self_attn.out_proj.weight, std=proj_std)
                init.normal_(layer.mlp.fc1.weight, std=fc_std)
                init.normal_(layer.mlp.fc2.weight, std=proj_std)
        elif isinstance(module, OneFormerTextEncoder):
            init.normal_(module.token_embedding.weight, std=0.02)
            init.normal_(module.positional_embedding, std=0.01)
        if hasattr(module, "reference_points"):
            init.xavier_uniform_(module.reference_points.weight, gain=1.0)
            init.constant_(module.reference_points.bias, 0.0)
        elif isinstance(module, OneFormerMLPPredictionHead):
            for submodule in module.modules():
                if isinstance(submodule, nn.Linear):
                    init.xavier_uniform_(submodule.weight, gain=xavier_std)
                    init.constant_(submodule.bias, 0)
        elif isinstance(module, nn.MultiheadAttention):
            init.normal_(module.in_proj_weight, mean=0.0, std=std)
            init.zeros_(module.in_proj_bias)
        elif isinstance(module, (nn.Linear, nn.Conv2d, nn.BatchNorm2d)):
            init.normal_(module.weight, mean=0.0, std=std)
            if module.bias is not None:
                init.zeros_(module.bias)
            if getattr(module, "running_mean", None) is not None:
                init.zeros_(module.running_mean)
                init.ones_(module.running_var)
                init.zeros_(module.num_batches_tracked)
        elif isinstance(module, (nn.LayerNorm, nn.GroupNorm)):
            init.ones_(module.weight)
            init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            init.normal_(module.weight, mean=0.0, std=std)
            # Here we need the check explicitly, as we slice the weight in the `zeros_` call, so it looses the flag
            if module.padding_idx is not None and not getattr(module.weight, "_is_hf_initialized", False):
                init.zeros_(module.weight[module.padding_idx])
        elif isinstance(module, OneFormerLoss):
            init.constant_(module.logit_scale, np.log(1 / self.config.contrastive_temperature))
            empty_weight = torch.ones(module.num_classes + 1)
            empty_weight[-1] = module.eos_coef
            init.copy_(module.empty_weight, empty_weight)