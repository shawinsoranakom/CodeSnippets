def forward(self, x, position_ids=None, layer_type=None):
        if layer_type is not None:
            raise ValueError(
                f"{self.__class__.__name__} does not support layer types, but got `layer_type={layer_type}`"
            )

        mscale = None
        seq_len = torch.max(position_ids) + 1
        if self.config.rope_parameters["rope_type"] != "default" and seq_len:
            mscale = (
                self.config.rope_parameters["long_mscale"]
                if seq_len > self.config.rope_parameters["original_max_position_embeddings"]
                else self.config.rope_parameters["short_mscale"]
            )
        inv_freq, attention_scaling = self.rope_init_fn(self.config, x.device, seq_len)
        mscale = attention_scaling if mscale is None else mscale
        inv_freq_expanded = inv_freq[None, :, None].float().expand(position_ids.shape[0], -1, 1).to(x.device)
        position_ids_expanded = position_ids[:, None, :].float()

        device_type = x.device.type if isinstance(x.device.type, str) and x.device.type != "mps" else "cpu"
        with maybe_autocast(device_type=device_type, enabled=False):  # Force float32
            freqs = (inv_freq_expanded.float() @ position_ids_expanded.float()).transpose(1, 2)
            emb = torch.cat((freqs, freqs), dim=-1)
            cos = emb.cos() * mscale
            sin = emb.sin() * mscale
        return cos.to(x.dtype), sin.to(x.dtype)