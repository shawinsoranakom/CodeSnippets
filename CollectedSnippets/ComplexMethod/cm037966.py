def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]) -> set[str]:
        stacked_params_mapping = [
            ("gate_up_proj", "gate_proj", 0),
            ("gate_up_proj", "up_proj", 1),
            ("fused_qkv_a_proj", "q_a_proj", 0),
            ("fused_qkv_a_proj", "kv_a_proj_with_mqa", 1),
        ]

        new_to_old_names_mapping = {
            "model.mtp.embed_tokens.weight": "model.layers.0.embed_tokens.weight",
            "model.mtp.layers.0.eh_proj.weight": "eh_proj.weight",
            "model.mtp.layers.0.eh_proj.weight_scale_inv": "eh_proj.weight_scale_inv",
            "model.mtp.layers.0.enorm.m.weight": "enorm.weight",
            "model.mtp.layers.0.hnorm.m.weight": "hnorm.weight",
            "model.mtp.layers.0.input_layernorm.weight": "model.layers.0.input_layernorm.weight",  # noqa: E501
            "model.mtp.layers.0.post_attention_layernorm.weight": "model.layers.0.post_attention_layernorm.weight",  # noqa: E501
            "model.mtp.layers.0.self_attn.kv_a_layernorm.weight": "model.layers.0.self_attn.kv_a_layernorm.weight",  # noqa: E501
            "model.mtp.layers.0.self_attn.kv_a_proj_with_mqa.weight": "model.layers.0.self_attn.kv_a_proj_with_mqa.weight",  # noqa: E501
            "model.mtp.layers.0.self_attn.kv_a_proj_with_mqa.weight_scale_inv": "model.layers.0.self_attn.kv_a_proj_with_mqa.weight_scale_inv",  # noqa: E501
            "model.mtp.layers.0.self_attn.kv_b_proj.weight": "model.layers.0.self_attn.kv_b_proj.weight",  # noqa: E501
            "model.mtp.layers.0.self_attn.kv_b_proj.weight_scale_inv": "model.layers.0.self_attn.kv_b_proj.weight_scale_inv",  # noqa: E501
            "model.mtp.layers.0.self_attn.o_proj.weight": "model.layers.0.self_attn.o_proj.weight",  # noqa: E501
            "model.mtp.layers.0.self_attn.o_proj.weight_scale_inv": "model.layers.0.self_attn.o_proj.weight_scale_inv",  # noqa: E501
            "model.mtp.layers.0.self_attn.q_a_layernorm.weight": "model.layers.0.self_attn.q_a_layernorm.weight",  # noqa: E501
            "model.mtp.layers.0.self_attn.q_a_proj.weight": "model.layers.0.self_attn.q_a_proj.weight",  # noqa: E501
            "model.mtp.layers.0.self_attn.q_a_proj.weight_scale_inv": "model.layers.0.self_attn.q_a_proj.weight_scale_inv",  # noqa: E501
            "model.mtp.layers.0.self_attn.q_b_proj.weight": "model.layers.0.self_attn.q_b_proj.weight",  # noqa: E501
            "model.mtp.layers.0.self_attn.q_b_proj.weight_scale_inv": "model.layers.0.self_attn.q_b_proj.weight_scale_inv",  # noqa: E501
            "model.mtp.layers.0.transformer_layer.mlp.down_proj.weight": "model.layers.0.mlp.down_proj.weight",  # noqa: E501
            "model.mtp.layers.0.transformer_layer.mlp.down_proj.weight_scale_inv": "model.layers.0.mlp.down_proj.weight_scale_inv",  # noqa: E501
            "model.mtp.layers.0.transformer_layer.mlp.gate_proj.weight": "model.layers.0.mlp.gate_proj.weight",  # noqa: E501
            "model.mtp.layers.0.transformer_layer.mlp.gate_proj.weight_scale_inv": "model.layers.0.mlp.gate_proj.weight_scale_inv",  # noqa: E501
            "model.mtp.layers.0.transformer_layer.mlp.up_proj.weight": "model.layers.0.mlp.up_proj.weight",  # noqa: E501
            "model.mtp.layers.0.transformer_layer.mlp.up_proj.weight_scale_inv": "model.layers.0.mlp.up_proj.weight_scale_inv",  # noqa: E501
            "model.mtp.norm.weight": "final_layernorm.weight",
        }

        params_dict = dict(self.named_parameters())
        loaded_params: set[str] = set()
        for name, loaded_weight in weights:
            if "rotary_emb.inv_freq" in name:
                continue
            spec_layer = self.get_spec_layer_idx_from_weight_name(self.config, name)
            if spec_layer is None:
                continue
            name = self._rewrite_spec_layer_name(
                spec_layer, name, new_to_old_names_mapping
            )
            for param_name, weight_name, shard_id in stacked_params_mapping:
                # Skip non-stacked layers and experts (experts handled below).
                if weight_name not in name:
                    continue
                # We have mlp.experts[0].gate_proj in the checkpoint.
                # Since we handle the experts below in expert_params_mapping,
                # we need to skip here BEFORE we update the name, otherwise
                # name will be updated to mlp.experts[0].gate_up_proj, which
                # will then be updated below in expert_params_mapping
                # for mlp.experts[0].gate_gate_up_proj, which breaks load.
                if ("mlp.experts." in name) and name not in params_dict:
                    continue
                name = name.replace(weight_name, param_name)

                # QKV fusion is optional, fall back to normal
                # weight loading if it's not enabled
                if (param_name == "fused_qkv_a_proj") and name not in params_dict:
                    continue

                # Skip loading extra bias for GPTQ models.
                if name.endswith(".bias") and name not in params_dict:
                    continue

                param = params_dict[name]
                weight_loader = param.weight_loader
                weight_loader(param, loaded_weight, shard_id)
                break
            else:
                # Skip loading extra bias for GPTQ models.
                if name.endswith(".bias") and name not in params_dict:
                    continue

                # According to DeepSeek-V3 Technical Report, MTP modules
                # shares embedding layer. We only load the first weights.
                if (
                    spec_layer != self.model.mtp_start_layer_idx
                    and ".layers" not in name
                ):
                    continue

                param = params_dict[name]
                weight_loader = getattr(param, "weight_loader", default_weight_loader)
                weight_loader(param, loaded_weight)
            loaded_params.add(name)
        spec_layer_id = self.config.num_hidden_layers * 2
        self_attn = self.model.layers[str(spec_layer_id)].mtp_block.self_attn
        if hasattr(
            self.quant_config, "weight_block_size"
        ) and self_attn.kv_b_proj.weight.dtype in (
            torch.float8_e4m3fn,
            torch.float8_e4m3fnuz,
        ):
            weight_block_size = self.quant_config.weight_block_size
            if weight_block_size is not None:
                dtype = torch.get_default_dtype()
                w = block_dequant(
                    self_attn.kv_b_proj.weight,
                    self_attn.kv_b_proj.weight_scale_inv,
                    weight_block_size,
                ).to(dtype)
            else:
                w = self_attn.kv_b_proj.weight
        else:
            w = self_attn.kv_b_proj.weight
        w_kc, w_vc = w.unflatten(
            0, (-1, self_attn.qk_nope_head_dim + self_attn.v_head_dim)
        ).split([self_attn.qk_nope_head_dim, self_attn.v_head_dim], dim=1)
        self_attn.w_kc = w_kc.transpose(1, 2).contiguous().transpose(1, 2)
        self_attn.w_vc = w_vc.contiguous().transpose(1, 2)
        if self.config.mla_scale_q_lora:
            self_attn.q_a_layernorm.weight.data *= (
                self.config.hidden_size / self.config.q_lora_rank
            ) ** 0.5
        if self.config.mla_scale_kv_lora:
            self_attn.kv_a_layernorm.weight.data *= (
                self.config.hidden_size / self.config.kv_lora_rank
            ) ** 0.5
        return loaded_params