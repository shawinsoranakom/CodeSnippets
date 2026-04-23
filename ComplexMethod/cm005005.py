def forward(
        self,
        hidden_states,
        cache_params: Cache | None = None,
        attention_mask: torch.Tensor | None = None,
        seq_idx: torch.IntTensor | None = None,
        **kwargs,
    ):
        if is_fast_path_available and "cuda" in self.in_proj.weight.device.type and not is_torchdynamo_compiling():
            return self.cuda_kernels_forward(hidden_states, cache_params, attention_mask, seq_idx)
        if seq_idx is not None:
            raise NotImplementedError(
                "`seq_idx` support requires fast path support. Please install `mamba_ssm` and `causal_conv1d`"
            )
        dtype = hidden_states.dtype
        if attention_mask is not None and attention_mask.shape[1] > 1 and attention_mask.shape[0] > 1:
            # tune out hidden states for pad tokens, see https://github.com/state-spaces/mamba/issues/66
            hidden_states = (hidden_states * attention_mask[:, :, None]).to(dtype)

        return self.torch_forward(hidden_states, cache_params, attention_mask)