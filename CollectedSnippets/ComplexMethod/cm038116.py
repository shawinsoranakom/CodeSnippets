def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]) -> set[str]:
        attn_mlp_replace_mapping = [
            (".qkv_proj", ".q_proj", "q"),
            (".qkv_proj", ".k_proj", "k"),
            (".qkv_proj", ".v_proj", "v"),
            (".fused_qkv_a_proj", ".q_a_proj", 0),
            (".fused_qkv_a_proj", ".kv_a_proj_with_mqa", 1),
            (".gate_up_proj", ".gate_proj", 0),
            (".gate_up_proj", ".up_proj", 1),
        ]
        has_experts = hasattr(self.config, "n_routed_experts")
        if has_experts:
            expert_merge_mapping = FusedMoE.make_expert_params_mapping(
                self,
                ckpt_gate_proj_name="gate_proj",
                ckpt_down_proj_name="down_proj",
                ckpt_up_proj_name="up_proj",
                num_experts=self.config.n_routed_experts,
                num_redundant_experts=self.num_redundant_experts,
            )

        params_dict = dict(self.named_parameters())
        loaded_params: set[str] = set()
        for name, loaded_weight in weights:
            if "rotary_emb.inv_freq" in name:
                continue
            if self.config.tie_word_embeddings and "lm_head.weight" in name:
                continue

            if (
                "layers" in name
                and hasattr(self.config, "num_nextn_predict_layers")
                and (self.config.num_nextn_predict_layers > 0)
            ):
                layer_idx = int(name.split("layers.")[-1].split(".")[0])
                mtp_idx = layer_idx - self.config.num_hidden_layers
                if mtp_idx >= 0 and mtp_idx < self.config.num_nextn_predict_layers:
                    continue  # skip spec decode layers for main model

            flag_dict = {"is_expert_weight": False}
            if (
                self.load_attn_mlp_weight(
                    attn_mlp_replace_mapping,
                    params_dict,
                    name,
                    loaded_weight,
                    loaded_params,
                )
                or has_experts
                and self.load_expert_weight(
                    expert_merge_mapping,
                    params_dict,
                    name,
                    loaded_weight,
                    loaded_params,
                    flag_dict,
                )
            ):
                continue
            else:
                if flag_dict["is_expert_weight"]:
                    continue
                if name.endswith(".bias") and name not in params_dict:
                    continue
                name = maybe_remap_kv_scale_name(name, params_dict)
                if name.endswith("e_score_correction_bias"):
                    name = name.replace(
                        "e_score_correction_bias", "gate.e_score_correction_bias"
                    )
                if name is None:
                    continue
                if is_pp_missing_parameter(name, self):
                    continue

                param = params_dict[name]
                weight_loader = getattr(param, "weight_loader", default_weight_loader)
                weight_loader(param, loaded_weight)
                loaded_params.add(name)

        self.post_weight_load()
        return loaded_params