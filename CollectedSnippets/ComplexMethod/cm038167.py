def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]):
        params_dict = dict(self.named_parameters())
        for name, loaded_weight in weights:
            # Both tie_word_embeddings=True and lm_head.weight in the safetensor
            # at the same time causes dict key access error.
            if name == "lm_head.weight" and self.config.tie_word_embeddings:
                assert "lm_head.weight" not in params_dict
                continue
            # Same workaround as AutoWeightsLoader for GPTQModel
            if any(
                substr in name
                for substr in AutoWeightsLoader.ROTARY_EMBEDS_UNUSED_WEIGHTS
            ):
                continue

            # Update the weight names to be compatible with the vllm version
            # of the model.
            # Do not change the order of the replacements.
            replacements = {
                # Rename incompatible weight names.
                ".A_log": ".A",
                ".B_norm_weight": ".B_norm.weight",
                ".C_norm_weight": ".C_norm.weight",
                ".dt_norm_weight": ".dt_norm.weight",
                ".q_weight": ".q_norm.weight",
                ".k_weight": ".k_norm.weight",
            }
            # Apply replacements based on the defined mappings
            for old, new in replacements.items():
                if old in name:
                    name = name.replace(old, new)

            # Reshape the in_proj weights to match the shape expected
            # by MergedColumnParallelLinear.
            # This works both for unquantized weights and
            # for quantized weights.
            # In the quantized case, the weights are already transposed.
            # Also, in addition to the quantized weights,
            # the zero points and scales have to be reshaped as well.
            # Packing should not be affected by this.
            if (
                ".mixer.in_proj.weight" in name
                or "mixer.in_proj.qweight" in name
                or "mixer.in_proj.scales" in name
                or "mixer.in_proj.qzeros" in name
            ):
                if "mixer.in_proj.weight" in name:
                    loaded_weight = loaded_weight.transpose(0, 1)
                # for weight:
                # loaded_weight.shape[0] == self.config.hidden_size
                # for qweight:
                # loaded_weight.shape[0] == self.config.hidden_size // param.pack_factor  # noqa
                # for scales and qzeros:
                # loaded_weight.shape[0] == self.config.hidden_size // self.vllm_config.quant_config.group_size  # noqa
                loaded_weight = loaded_weight.reshape(
                    loaded_weight.shape[0], self.config.mamba_num_heads, -1
                )
                gate_weight, hidden_states_weight = loaded_weight.chunk(2, dim=-1)
                gate_weight = gate_weight.reshape(loaded_weight.shape[0], -1)
                hidden_states_weight = hidden_states_weight.reshape(
                    loaded_weight.shape[0], -1
                )
                loaded_weight = torch.cat([gate_weight, hidden_states_weight], dim=-1)
                if "mixer.in_proj.weight" in name:
                    loaded_weight = loaded_weight.transpose(0, 1)

            # Offset parameter with vllm's RMSNorm haven't been supported yet.
            if ".pre_mixer_norm" in name:
                loaded_weight += 1.0
            elif ".post_mixer_norm" in name:
                loaded_weight += 1.0 / 5
            elif ".pre_mlp_norm" in name:
                loaded_weight += 1.0
            elif ".post_mlp_norm" in name:
                loaded_weight += 1.0 / (5**1.5)
            elif "model.norm.weight" in name:
                loaded_weight += 1.0

            # Skip layers on other devices.
            if is_pp_missing_parameter(name, self):
                continue

            param = params_dict[name]
            weight_loader = getattr(param, "weight_loader", default_weight_loader)
            weight_loader(param, loaded_weight)