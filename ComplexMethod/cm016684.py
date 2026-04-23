def forward(self,
                x,
                t,
                context,#encoder_hidden_states=None,
                text_embedding_mask=None,
                encoder_hidden_states_t5=None,
                text_embedding_mask_t5=None,
                image_meta_size=None,
                style=None,
                return_dict=False,
                control=None,
                transformer_options={},
                ):
        """
        Forward pass of the encoder.

        Parameters
        ----------
        x: torch.Tensor
            (B, D, H, W)
        t: torch.Tensor
            (B)
        encoder_hidden_states: torch.Tensor
            CLIP text embedding, (B, L_clip, D)
        text_embedding_mask: torch.Tensor
            CLIP text embedding mask, (B, L_clip)
        encoder_hidden_states_t5: torch.Tensor
            T5 text embedding, (B, L_t5, D)
        text_embedding_mask_t5: torch.Tensor
            T5 text embedding mask, (B, L_t5)
        image_meta_size: torch.Tensor
            (B, 6)
        style: torch.Tensor
            (B)
        cos_cis_img: torch.Tensor
        sin_cis_img: torch.Tensor
        return_dict: bool
            Whether to return a dictionary.
        """
        patches_replace = transformer_options.get("patches_replace", {})
        encoder_hidden_states = context
        text_states = encoder_hidden_states                     # 2,77,1024
        text_states_t5 = encoder_hidden_states_t5               # 2,256,2048
        text_states_mask = text_embedding_mask.bool()           # 2,77
        text_states_t5_mask = text_embedding_mask_t5.bool()     # 2,256
        b_t5, l_t5, c_t5 = text_states_t5.shape
        text_states_t5 = self.mlp_t5(text_states_t5.view(-1, c_t5)).view(b_t5, l_t5, -1)

        padding = comfy.ops.cast_to_input(self.text_embedding_padding, text_states)

        text_states[:,-self.text_len:] = torch.where(text_states_mask[:,-self.text_len:].unsqueeze(2), text_states[:,-self.text_len:], padding[:self.text_len])
        text_states_t5[:,-self.text_len_t5:] = torch.where(text_states_t5_mask[:,-self.text_len_t5:].unsqueeze(2), text_states_t5[:,-self.text_len_t5:], padding[self.text_len:])

        text_states = torch.cat([text_states, text_states_t5], dim=1)  # 2,205，1024
        # clip_t5_mask = torch.cat([text_states_mask, text_states_t5_mask], dim=-1)

        _, _, oh, ow = x.shape
        th, tw = (oh + (self.patch_size // 2)) // self.patch_size, (ow + (self.patch_size // 2)) // self.patch_size


        # Get image RoPE embedding according to `reso`lution.
        freqs_cis_img = calc_rope(x, self.patch_size, self.hidden_size // self.num_heads) #(cos_cis_img, sin_cis_img)

        # ========================= Build time and image embedding =========================
        t = self.t_embedder(t, dtype=x.dtype)
        x = self.x_embedder(x)

        # ========================= Concatenate all extra vectors =========================
        # Build text tokens with pooling
        extra_vec = self.pooler(encoder_hidden_states_t5)

        # Build image meta size tokens if applicable
        if self.size_cond:
            image_meta_size = timestep_embedding(image_meta_size.view(-1), 256).to(x.dtype)   # [B * 6, 256]
            image_meta_size = image_meta_size.view(-1, 6 * 256)
            extra_vec = torch.cat([extra_vec, image_meta_size], dim=1)  # [B, D + 6 * 256]

        # Build style tokens
        if self.use_style_cond:
            if style is None:
                style = torch.zeros((extra_vec.shape[0],), device=x.device, dtype=torch.int)
            style_embedding = self.style_embedder(style, out_dtype=x.dtype)
            extra_vec = torch.cat([extra_vec, style_embedding], dim=1)

        # Concatenate all extra vectors
        c = t + self.extra_embedder(extra_vec)  # [B, D]

        blocks_replace = patches_replace.get("dit", {})

        controls = None
        if control:
            controls = control.get("output", None)
        # ========================= Forward pass through HunYuanDiT blocks =========================
        skips = []
        for layer, block in enumerate(self.blocks):
            if layer > self.depth // 2:
                if controls is not None:
                    skip = skips.pop() + controls.pop().to(dtype=x.dtype)
                else:
                    skip = skips.pop()
            else:
                skip = None

            if ("double_block", layer) in blocks_replace:
                def block_wrap(args):
                    out = {}
                    out["img"] = block(args["img"], args["vec"], args["txt"], args["pe"], args["skip"])
                    return out

                out = blocks_replace[("double_block", layer)]({"img": x, "txt": text_states, "vec": c, "pe": freqs_cis_img, "skip": skip}, {"original_block": block_wrap})
                x = out["img"]
            else:
                x = block(x, c, text_states, freqs_cis_img, skip)   # (N, L, D)


            if layer < (self.depth // 2 - 1):
                skips.append(x)
        if controls is not None and len(controls) != 0:
            raise ValueError("The number of controls is not equal to the number of skip connections.")

        # ========================= Final layer =========================
        x = self.final_layer(x, c)                              # (N, L, patch_size ** 2 * out_channels)
        x = self.unpatchify(x, th, tw)                          # (N, out_channels, H, W)

        if return_dict:
            return {'x': x}
        if self.learn_sigma:
            return x[:,:self.out_channels // 2,:oh,:ow]
        return x[:,:,:oh,:ow]