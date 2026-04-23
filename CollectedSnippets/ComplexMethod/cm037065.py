def get_head_size(self) -> int:
        if self.is_deepseek_mla():
            qk_rope_head_dim = getattr(self.hf_text_config, "qk_rope_head_dim", 0)
            if not envs.VLLM_MLA_DISABLE:
                return self.hf_text_config.kv_lora_rank + qk_rope_head_dim
            else:
                qk_nope_head_dim = getattr(self.hf_text_config, "qk_nope_head_dim", 0)
                if qk_rope_head_dim and qk_nope_head_dim:
                    return qk_rope_head_dim + qk_nope_head_dim

        # NOTE: Some configs may set head_dim=None in the config
        if getattr(self.hf_text_config, "head_dim", None) is not None:
            return self.hf_text_config.head_dim

        # NOTE: Some models (such as PLaMo2.1) use `hidden_size_per_head`
        if getattr(self.hf_text_config, "hidden_size_per_head", None) is not None:
            return self.hf_text_config.hidden_size_per_head

        if (total_num_attention_heads := self.get_total_num_attention_heads()) == 0:
            return 0
        # FIXME(woosuk): This may not be true for all models.
        return self.get_hidden_size() // total_num_attention_heads