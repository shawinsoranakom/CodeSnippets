def forward(
        self,
        x,
        timesteps,
        context,
        attention_mask=None,
        guidance: torch.Tensor = None,
        hint=None,
        transformer_options={},
        base_model=None,
        **kwargs,
    ):
        if base_model is None:
            raise RuntimeError("Qwen Fun ControlNet requires a QwenImage base model at runtime.")

        encoder_hidden_states_mask = attention_mask
        # Keep attention mask disabled inside Fun control blocks to mirror
        # VideoX behavior (they rely on seq lengths for RoPE, not masked attention).
        encoder_hidden_states_mask = None

        hidden_states, img_ids, _ = base_model.process_img(x)
        hint_tokens = self._process_hint_tokens(hint)
        if hint_tokens is None:
            raise RuntimeError("Qwen Fun ControlNet requires a control hint image.")

        if hint_tokens.shape[1] != hidden_states.shape[1]:
            max_tokens = min(hint_tokens.shape[1], hidden_states.shape[1])
            hint_tokens = hint_tokens[:, :max_tokens]
            hidden_states = hidden_states[:, :max_tokens]
            img_ids = img_ids[:, :max_tokens]

        txt_start = round(
            max(
                ((x.shape[-1] + (base_model.patch_size // 2)) // base_model.patch_size) // 2,
                ((x.shape[-2] + (base_model.patch_size // 2)) // base_model.patch_size) // 2,
            )
        )
        txt_ids = torch.arange(txt_start, txt_start + context.shape[1], device=x.device).reshape(1, -1, 1).repeat(x.shape[0], 1, 3)
        ids = torch.cat((txt_ids, img_ids), dim=1)
        image_rotary_emb = base_model.pe_embedder(ids).to(x.dtype).contiguous()

        hidden_states = base_model.img_in(hidden_states)
        encoder_hidden_states = base_model.txt_norm(context)
        encoder_hidden_states = base_model.txt_in(encoder_hidden_states)

        if guidance is not None:
            guidance = guidance * 1000

        temb = (
            base_model.time_text_embed(timesteps, hidden_states)
            if guidance is None
            else base_model.time_text_embed(timesteps, guidance, hidden_states)
        )

        c = self.control_img_in(hint_tokens)

        for i, block in enumerate(self.control_blocks):
            if i == 0:
                c_in = block.before_proj(c) + hidden_states
                all_c = []
            else:
                all_c = list(torch.unbind(c, dim=0))
                c_in = all_c.pop(-1)

            encoder_hidden_states, c_out = block(
                hidden_states=c_in,
                encoder_hidden_states=encoder_hidden_states,
                encoder_hidden_states_mask=encoder_hidden_states_mask,
                temb=temb,
                image_rotary_emb=image_rotary_emb,
                transformer_options=transformer_options,
            )

            c_skip = block.after_proj(c_out) * self.hint_scale
            all_c += [c_skip, c_out]
            c = torch.stack(all_c, dim=0)

        hints = torch.unbind(c, dim=0)[:-1]

        controlnet_block_samples = [None] * self.main_model_double
        for local_idx, base_idx in enumerate(self.injection_layers):
            if local_idx < len(hints) and base_idx < len(controlnet_block_samples):
                controlnet_block_samples[base_idx] = hints[local_idx]

        return {"input": controlnet_block_samples}