def forward(  # x, prompt_x, x_lens, t, style,cond
        self,  # d is channel,n is T
        x0: float["b n d"],  # nosied input audio  # noqa: F722
        cond0: float["b n d"],  # masked cond audio  # noqa: F722
        x_lens,
        time: float["b"] | float[""],  # time step  # noqa: F821 F722
        dt_base_bootstrap,
        text0,  # : int["b nt"]  # noqa: F722#####condition feature
        use_grad_ckpt=False,  # bool
        ###no-use
        drop_audio_cond=False,  # cfg for cond audio
        drop_text=False,  # cfg for text
        # mask: bool["b n"] | None = None,  # noqa: F722
        infer=False,  # bool
        text_cache=None,  # torch tensor as text_embed
        dt_cache=None,  # torch tensor as dt
    ):
        x = x0.transpose(2, 1)
        cond = cond0.transpose(2, 1)
        text = text0.transpose(2, 1)
        mask = sequence_mask(x_lens, max_length=x.size(1)).to(x.device)

        batch, seq_len = x.shape[0], x.shape[1]
        if time.ndim == 0:
            time = time.repeat(batch)

        # t: conditioning time, c: context (text + masked cond audio), x: noised input audio
        t = self.time_embed(time)
        if infer and dt_cache is not None:
            dt = dt_cache
        else:
            dt = self.d_embed(dt_base_bootstrap)
        t += dt

        if infer and text_cache is not None:
            text_embed = text_cache
        else:
            text_embed = self.text_embed(text, seq_len, drop_text=drop_text)  ###need to change

        x = self.input_embed(x, cond, text_embed, drop_audio_cond=drop_audio_cond)

        rope = self.rotary_embed.forward_from_seq_len(seq_len)

        if self.long_skip_connection is not None:
            residual = x

        for block in self.transformer_blocks:
            if use_grad_ckpt:
                x = checkpoint(self.ckpt_wrapper(block), x, t, mask, rope, use_reentrant=False)
            else:
                x = block(x, t, mask=mask, rope=rope)

        if self.long_skip_connection is not None:
            x = self.long_skip_connection(torch.cat((x, residual), dim=-1))

        x = self.norm_out(x, t)
        output = self.proj_out(x)

        if infer:
            return output, text_embed, dt
        else:
            return output