def forward_orig(
        self,
        x,
        t,
        context,
        audio_embed=None,
        reference_latent=None,
        control_video=None,
        reference_motion=None,
        clip_fea=None,
        freqs=None,
        transformer_options={},
        **kwargs,
    ):
        if audio_embed is not None:
            num_embeds = x.shape[-3] * 4
            audio_emb_global, audio_emb = self.casual_audio_encoder(audio_embed[:, :, :, :num_embeds])
        else:
            audio_emb = None

        # embeddings
        bs, _, time, height, width = x.shape
        x = self.patch_embedding(x.float()).to(x.dtype)
        if control_video is not None:
            x = x + self.cond_encoder(control_video)

        if t.ndim == 1:
            t = t.unsqueeze(1).repeat(1, x.shape[2])

        grid_sizes = x.shape[2:]
        x = x.flatten(2).transpose(1, 2)
        seq_len = x.size(1)

        cond_mask_weight = comfy.model_management.cast_to(self.trainable_cond_mask.weight, dtype=x.dtype, device=x.device).unsqueeze(1).unsqueeze(1)
        x = x + cond_mask_weight[0]

        if reference_latent is not None:
            ref = self.patch_embedding(reference_latent.float()).to(x.dtype)
            ref = ref.flatten(2).transpose(1, 2)
            freqs_ref = self.rope_encode(reference_latent.shape[-3], reference_latent.shape[-2], reference_latent.shape[-1], t_start=max(30, time + 9), device=x.device, dtype=x.dtype)
            ref = ref + cond_mask_weight[1]
            x = torch.cat([x, ref], dim=1)
            freqs = torch.cat([freqs, freqs_ref], dim=1)
            t = torch.cat([t, torch.zeros((t.shape[0], reference_latent.shape[-3]), device=t.device, dtype=t.dtype)], dim=1)
            del ref, freqs_ref

        if reference_motion is not None:
            motion_encoded, freqs_motion = self.frame_packer(reference_motion, self)
            motion_encoded = motion_encoded + cond_mask_weight[2]
            x = torch.cat([x, motion_encoded], dim=1)
            freqs = torch.cat([freqs, freqs_motion], dim=1)

            t = torch.repeat_interleave(t, 2, dim=1)
            t = torch.cat([t, torch.zeros((t.shape[0], 3), device=t.device, dtype=t.dtype)], dim=1)
            del motion_encoded, freqs_motion

        # time embeddings
        e = self.time_embedding(
            sinusoidal_embedding_1d(self.freq_dim, t.flatten()).to(dtype=x[0].dtype))
        e = e.reshape(t.shape[0], -1, e.shape[-1])
        e0 = self.time_projection(e).unflatten(2, (6, self.dim))

        # context
        context = self.text_embedding(context)

        patches_replace = transformer_options.get("patches_replace", {})
        blocks_replace = patches_replace.get("dit", {})
        transformer_options["total_blocks"] = len(self.blocks)
        transformer_options["block_type"] = "double"
        for i, block in enumerate(self.blocks):
            transformer_options["block_index"] = i
            if ("double_block", i) in blocks_replace:
                def block_wrap(args):
                    out = {}
                    out["img"] = block(args["img"], context=args["txt"], e=args["vec"], freqs=args["pe"], transformer_options=args["transformer_options"])
                    return out
                out = blocks_replace[("double_block", i)]({"img": x, "txt": context, "vec": e0, "pe": freqs, "transformer_options": transformer_options}, {"original_block": block_wrap})
                x = out["img"]
            else:
                x = block(x, e=e0, freqs=freqs, context=context, transformer_options=transformer_options)
            if audio_emb is not None:
                x = self.audio_injector(x, i, audio_emb, audio_emb_global, seq_len)
        # head
        x = self.head(x, e)

        # unpatchify
        x = self.unpatchify(x, grid_sizes)
        return x