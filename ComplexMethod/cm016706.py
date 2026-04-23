def forward_orig(self, x, t, context, clip_fea=None, freqs=None, transformer_options={}, pose_latents=None, reference_latent=None, **kwargs):

        if reference_latent is not None:
            x = torch.cat((reference_latent, x), dim=2)

        # embeddings
        x = self.patch_embedding(x.float()).to(x.dtype)
        grid_sizes = x.shape[2:]
        transformer_options["grid_sizes"] = grid_sizes
        x = x.flatten(2).transpose(1, 2)

        scail_pose_seq_len = 0
        if pose_latents is not None:
            scail_x = self.patch_embedding_pose(pose_latents.float()).to(x.dtype)
            scail_x = scail_x.flatten(2).transpose(1, 2)
            scail_pose_seq_len = scail_x.shape[1]
            x = torch.cat([x, scail_x], dim=1)
            del scail_x

        # time embeddings
        e = self.time_embedding(sinusoidal_embedding_1d(self.freq_dim, t.flatten()).to(dtype=x[0].dtype))
        e = e.reshape(t.shape[0], -1, e.shape[-1])
        e0 = self.time_projection(e).unflatten(2, (6, self.dim))

        # context
        context = self.text_embedding(context)

        context_img_len = None
        if clip_fea is not None:
            if self.img_emb is not None:
                context_clip = self.img_emb(clip_fea)  # bs x 257 x dim
                context = torch.cat([context_clip, context], dim=1)
            context_img_len = clip_fea.shape[-2]

        patches_replace = transformer_options.get("patches_replace", {})
        blocks_replace = patches_replace.get("dit", {})
        transformer_options["total_blocks"] = len(self.blocks)
        transformer_options["block_type"] = "double"
        for i, block in enumerate(self.blocks):
            transformer_options["block_index"] = i
            if ("double_block", i) in blocks_replace:
                def block_wrap(args):
                    out = {}
                    out["img"] = block(args["img"], context=args["txt"], e=args["vec"], freqs=args["pe"], context_img_len=context_img_len, transformer_options=args["transformer_options"])
                    return out
                out = blocks_replace[("double_block", i)]({"img": x, "txt": context, "vec": e0, "pe": freqs, "transformer_options": transformer_options}, {"original_block": block_wrap})
                x = out["img"]
            else:
                x = block(x, e=e0, freqs=freqs, context=context, context_img_len=context_img_len, transformer_options=transformer_options)

        # head
        x = self.head(x, e)

        if scail_pose_seq_len > 0:
            x = x[:, :-scail_pose_seq_len]

        # unpatchify
        x = self.unpatchify(x, grid_sizes)

        if reference_latent is not None:
            x = x[:, :, reference_latent.shape[2]:]

        return x