def uses_alibi(self) -> bool:
        cfg = self.hf_text_config

        return (
            getattr(cfg, "alibi", False)  # Falcon
            or "BloomForCausalLM" in self.architectures  # Bloom
            or getattr(cfg, "position_encoding_type", "") == "alibi"  # codellm_1b_alibi
            or (
                hasattr(cfg, "attn_config")  # MPT
                and (
                    (
                        isinstance(cfg.attn_config, dict)
                        and cfg.attn_config.get("alibi", False)
                    )
                    or (
                        not isinstance(cfg.attn_config, dict)
                        and getattr(cfg.attn_config, "alibi", False)
                    )
                )
            )
        )