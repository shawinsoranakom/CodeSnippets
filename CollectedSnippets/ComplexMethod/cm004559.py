def _init_weights(self, module):
        """Initialize the weights"""
        if isinstance(module, nn.Linear):
            init.normal_(module.weight, std=1.0 / math.sqrt(module.weight.size(1)))
            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, nn.Conv1d):
            init.kaiming_normal_(module.weight)
            if module.bias is not None:
                key = math.sqrt(module.groups / (module.in_channels * module.kernel_size[0]))
                init.uniform_(module.bias, a=-key, b=key)
        elif isinstance(module, (nn.LayerNorm, nn.BatchNorm1d)):
            init.zeros_(module.bias)
            init.ones_(module.weight)
            if getattr(module, "running_mean", None) is not None:
                init.zeros_(module.running_mean)
                init.ones_(module.running_var)
                init.zeros_(module.num_batches_tracked)
        elif isinstance(module, nn.Embedding):
            init.normal_(module.weight)
            # Here we need the check explicitly, as we slice the weight in the `zeros_` call, so it looses the flag
            if module.padding_idx is not None and not getattr(module.weight, "_is_hf_initialized", False):
                init.zeros_(module.weight[module.padding_idx])
        elif isinstance(module, FastSpeech2ConformerAttention):
            init.xavier_uniform_(module.pos_bias_u)
            init.xavier_uniform_(module.pos_bias_v)
        elif isinstance(module, FastSpeech2ConformerRelPositionalEncoding):
            init.copy_(module.pos_enc, module.extend_pos_enc(torch.tensor(0.0).expand(1, module.max_len)))