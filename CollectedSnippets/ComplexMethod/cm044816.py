def forward(
        self,
        x: float["b n d"],  # nosied input audio  # noqa: F722
        cond: float["b n d"],  # masked cond audio  # noqa: F722
        text: int["b nt"],  # text  # noqa: F722
        time: float["b"] | float[""],  # time step  # noqa: F821 F722
        drop_audio_cond,  # cfg for cond audio
        drop_text,  # cfg for text
        mask: bool["b n"] | None = None,  # noqa: F722
    ):
        batch, seq_len = x.shape[0], x.shape[1]
        if time.ndim == 0:
            time = time.repeat(batch)

        # t: conditioning time, c: context (text + masked cond audio), x: noised input audio
        t = self.time_embed(time)
        text_embed = self.text_embed(text, seq_len, drop_text=drop_text)
        x = self.input_embed(x, cond, text_embed, drop_audio_cond=drop_audio_cond)

        # postfix time t to input x, [b n d] -> [b n+1 d]
        x = torch.cat([t.unsqueeze(1), x], dim=1)  # pack t to x
        if mask is not None:
            mask = F.pad(mask, (1, 0), value=1)

        rope = self.rotary_embed.forward_from_seq_len(seq_len + 1)

        # flat unet transformer
        skip_connect_type = self.skip_connect_type
        skips = []
        for idx, (maybe_skip_proj, attn_norm, attn, ff_norm, ff) in enumerate(self.layers):
            layer = idx + 1

            # skip connection logic
            is_first_half = layer <= (self.depth // 2)
            is_later_half = not is_first_half

            if is_first_half:
                skips.append(x)

            if is_later_half:
                skip = skips.pop()
                if skip_connect_type == "concat":
                    x = torch.cat((x, skip), dim=-1)
                    x = maybe_skip_proj(x)
                elif skip_connect_type == "add":
                    x = x + skip

            # attention and feedforward blocks
            x = attn(attn_norm(x), rope=rope, mask=mask) + x
            x = ff(ff_norm(x)) + x

        assert len(skips) == 0

        x = self.norm_out(x)[:, 1:, :]  # unpack t from x

        return self.proj_out(x)