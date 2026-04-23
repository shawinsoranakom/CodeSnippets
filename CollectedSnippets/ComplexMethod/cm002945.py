def forward(
        self,
        input_ids=None,
        attention_mask=None,
        use_audio_in_video=None,
        audio_feature_lengths=None,
        video_second_per_grid=None,
        image_grid_thw=None,
        video_grid_thw=None,
        position_ids=None,
        past_key_values=None,
        inputs_embeds=None,
        labels=None,
        use_cache=None,
        output_router_logits=None,
        residual_codes=None,
        trailing_text_hidden=None,
        tts_pad_embed=None,
        generation_step=None,
        talker_input_ids=None,
        **kwargs,
    ) -> MoeCausalLMOutputWithPast:
        r"""
        use_audio_in_video (`bool`, *optional*):
            If set to `True`, use the audio in video.
        audio_feature_lengths (`torch.LongTensor` of shape `(num_audios)`, *optional*):
            The length of feature shape of each audio in LLM.
        video_second_per_grid (`torch.LongTensor` of shape `(num_videos)`, *optional*):
            Number of seconds per grid for each video, used for temporal feature mapping.
        image_grid_thw (`torch.LongTensor` of shape `(num_images, 3)`, *optional*):
            The temporal, height and width of feature shape of each image in LLM.
        video_grid_thw (`torch.LongTensor` of shape `(num_videos, 3)`, *optional*):
            The temporal, height and width of feature shape of each video in LLM.
        residual_codes (`torch.Tensor`):
            The predicted residual codes of previous step.
        trailing_text_hidden (`torch.Tensor`):
            Text hidden states from thinker after the first token.
        tts_pad_embed (`torch.Tensor`):
            Embedding tensor of `tts_pad_token_id`.
        generation_step (`int`):
            Generation step since prefill, used to sync with `trailing_text_hidden`.
        talker_input_ids (`torch.Tensor`):
            Input ids from thinker, used to compute 3d RoPE.
        """
        # Prefill
        if inputs_embeds is not None and inputs_embeds.shape[1] > 1:
            generation_step = -1
            residual_codes = None
        if position_ids is None:
            past_key_values_length = 0 if past_key_values is None else past_key_values.get_seq_length()
            if past_key_values_length == 0 or self.rope_deltas is None:
                delta0 = (1 - attention_mask).sum(dim=-1).unsqueeze(1)
                position_ids, rope_deltas = self.get_rope_index(
                    talker_input_ids,
                    image_grid_thw,
                    video_grid_thw,
                    attention_mask,
                    use_audio_in_video,
                    audio_feature_lengths,
                    video_second_per_grid,
                )
                rope_deltas = rope_deltas - delta0
                self.rope_deltas = rope_deltas
            else:
                batch_size, seq_length = input_ids.shape
                delta = (past_key_values_length + self.rope_deltas).to(input_ids.device)
                position_ids = torch.arange(seq_length, device=input_ids.device)
                position_ids = position_ids.view(1, -1).expand(batch_size, -1)
                position_ids = position_ids.add(delta)
                position_ids = position_ids.unsqueeze(0).expand(3, -1, -1)

        outputs: MoeModelOutputWithPast = self.model(
            input_ids=None,
            attention_mask=attention_mask,
            position_ids=position_ids,
            past_key_values=past_key_values,
            inputs_embeds=inputs_embeds,
            use_cache=use_cache,
            output_router_logits=output_router_logits,
            **kwargs,
        )

        hidden_states = outputs.last_hidden_state
        logits = self.codec_head(hidden_states)

        loss = None
        if labels is not None:
            loss = self.loss_function(logits=logits, labels=labels, vocab_size=self.config.vocab_size, **kwargs)

        aux_loss = None
        if output_router_logits:
            aux_loss = load_balancing_loss_func(
                outputs.router_logits,
                self.num_experts,
                self.num_experts_per_tok,
                attention_mask,
            )
            if labels is not None:
                loss += self.router_aux_loss_coef * aux_loss.to(loss.device)  # make sure to reside in the same device

        return Qwen3OmniMoeTalkerOutputWithPast(
            loss=loss,
            logits=logits,
            aux_loss=aux_loss,
            past_key_values=outputs.past_key_values,
            hidden_states=(
                outputs.hidden_states,
                residual_codes,
            ),  # TODO: hack here to take residual codes out, need refactor.
            generation_step=generation_step + 1,
        )