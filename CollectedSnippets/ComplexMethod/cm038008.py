def maybe_remap_mistral(
        self,
        name: str,
        loaded_weight: torch.Tensor,
    ) -> tuple[str, torch.Tensor]:
        def permute(w: torch.Tensor, n_heads: int, attn_out: int):
            attn_in = self.config.head_dim * n_heads

            return (
                w.view(n_heads, attn_in // n_heads // 2, 2, attn_out)
                .transpose(1, 2)
                .reshape(attn_in, attn_out)
            )

        mapping = self.mistral_mapping
        modules = name.split(".")

        # rotary embeds should be sliced
        # If using quantized model in mistral format,
        # quantization scales (qscale_weight) also need to be sliced
        if "wk" in modules and modules[-1] == "weight":
            loaded_weight = permute(
                loaded_weight, self.config.num_key_value_heads, self.config.hidden_size
            )
        elif (
            "wk" in modules
            and modules[-1] == "qscale_weight"
            and loaded_weight.numel() > 1
        ):
            loaded_weight = permute(loaded_weight, self.config.num_key_value_heads, 1)
        elif "wq" in modules and modules[-1] == "weight":
            loaded_weight = permute(
                loaded_weight, self.config.num_attention_heads, self.config.hidden_size
            )
        elif (
            "wq" in modules
            and modules[-1] == "qscale_weight"
            and loaded_weight.numel() > 1
        ):
            loaded_weight = permute(loaded_weight, self.config.num_attention_heads, 1)

        num_modules = len(modules)
        for i in range(num_modules):
            item = modules[i]
            next_item = modules[i + 1] if i < num_modules - 1 else None

            combined_item = f"{item}.{next_item}" if next_item is not None else None

            if combined_item in mapping:
                name = name.replace(combined_item, mapping[combined_item])
            elif item in mapping and mapping[item] not in name:
                name = name.replace(item, mapping[item])

        return name, loaded_weight