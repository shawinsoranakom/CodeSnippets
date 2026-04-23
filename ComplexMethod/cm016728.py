def forward(
        self,
        x: torch.Tensor,
        context: Optional[torch.Tensor] = None,
        time_context: Optional[torch.Tensor] = None,
        timesteps: Optional[int] = None,
        image_only_indicator: Optional[torch.Tensor] = None,
        transformer_options={}
    ) -> torch.Tensor:
        _, _, h, w = x.shape
        transformer_options["activations_shape"] = list(x.shape)
        x_in = x
        spatial_context = None
        if exists(context):
            spatial_context = context

        if self.use_spatial_context:
            assert (
                context.ndim == 3
            ), f"n dims of spatial context should be 3 but are {context.ndim}"

            if time_context is None:
                time_context = context
            time_context_first_timestep = time_context[::timesteps]
            time_context = repeat(
                time_context_first_timestep, "b ... -> (b n) ...", n=h * w
            )
        elif time_context is not None and not self.use_spatial_context:
            time_context = repeat(time_context, "b ... -> (b n) ...", n=h * w)
            if time_context.ndim == 2:
                time_context = rearrange(time_context, "b c -> b 1 c")

        x = self.norm(x)
        if not self.use_linear:
            x = self.proj_in(x)
        x = rearrange(x, "b c h w -> b (h w) c")
        if self.use_linear:
            x = self.proj_in(x)

        num_frames = torch.arange(timesteps, device=x.device)
        num_frames = repeat(num_frames, "t -> b t", b=x.shape[0] // timesteps)
        num_frames = rearrange(num_frames, "b t -> (b t)")
        t_emb = timestep_embedding(num_frames, self.in_channels, repeat_only=False, max_period=self.max_time_embed_period).to(x.dtype)
        emb = self.time_pos_embed(t_emb)
        emb = emb[:, None, :]

        for it_, (block, mix_block) in enumerate(
            zip(self.transformer_blocks, self.time_stack)
        ):
            transformer_options["block_index"] = it_
            x = block(
                x,
                context=spatial_context,
                transformer_options=transformer_options,
            )

            x_mix = x
            x_mix = x_mix + emb

            B, S, C = x_mix.shape
            x_mix = rearrange(x_mix, "(b t) s c -> (b s) t c", t=timesteps)
            x_mix = mix_block(x_mix, context=time_context, transformer_options=transformer_options)
            x_mix = rearrange(
                x_mix, "(b s) t c -> (b t) s c", s=S, b=B // timesteps, c=C, t=timesteps
            )

            x = self.time_mixer(x_spatial=x, x_temporal=x_mix, image_only_indicator=image_only_indicator)

        if self.use_linear:
            x = self.proj_out(x)
        x = rearrange(x, "b (h w) c -> b c h w", h=h, w=w)
        if not self.use_linear:
            x = self.proj_out(x)
        out = x + x_in
        return out