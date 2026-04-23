def forward(
        self,
        x,
        mask = None,
        prepend_embeds = None,
        prepend_mask = None,
        global_cond = None,
        return_info = False,
        **kwargs
    ):
        transformer_options = kwargs.get("transformer_options", {})
        patches_replace = transformer_options.get("patches_replace", {})
        batch, seq, device = *x.shape[:2], x.device
        context = kwargs["context"]

        info = {
            "hidden_states": [],
        }

        x = self.project_in(x)

        if prepend_embeds is not None:
            prepend_length, prepend_dim = prepend_embeds.shape[1:]

            assert prepend_dim == x.shape[-1], 'prepend dimension must match sequence dimension'

            x = torch.cat((prepend_embeds, x), dim = -2)

            if prepend_mask is not None or mask is not None:
                mask = mask if mask is not None else torch.ones((batch, seq), device = device, dtype = torch.bool)
                prepend_mask = prepend_mask if prepend_mask is not None else torch.ones((batch, prepend_length), device = device, dtype = torch.bool)

                mask = torch.cat((prepend_mask, mask), dim = -1)

        # Attention layers

        if self.rotary_pos_emb is not None:
            rotary_pos_emb = self.rotary_pos_emb.forward_from_seq_len(x.shape[1], dtype=torch.float, device=x.device)
        else:
            rotary_pos_emb = None

        if self.use_sinusoidal_emb or self.use_abs_pos_emb:
            x = x + self.pos_emb(x)

        blocks_replace = patches_replace.get("dit", {})
        # Iterate over the transformer layers
        for i, layer in enumerate(self.layers):
            if ("double_block", i) in blocks_replace:
                def block_wrap(args):
                    out = {}
                    out["img"] = layer(args["img"], rotary_pos_emb=args["pe"], global_cond=args["vec"], context=args["txt"], transformer_options=args["transformer_options"])
                    return out

                out = blocks_replace[("double_block", i)]({"img": x, "txt": context, "vec": global_cond, "pe": rotary_pos_emb, "transformer_options": transformer_options}, {"original_block": block_wrap})
                x = out["img"]
            else:
                x = layer(x, rotary_pos_emb = rotary_pos_emb, global_cond=global_cond, context=context, transformer_options=transformer_options)
            # x = checkpoint(layer, x, rotary_pos_emb = rotary_pos_emb, global_cond=global_cond, **kwargs)

            if return_info:
                info["hidden_states"].append(x)

        x = self.project_out(x)

        if return_info:
            return x, info

        return x