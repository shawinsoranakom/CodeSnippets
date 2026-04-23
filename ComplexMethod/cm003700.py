def forward(
        self,
        input_features: torch.FloatTensor,
        input_ids: torch.LongTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        attention_mask: torch.LongTensor | None = None,
    ):
        # process text
        if input_ids is not None and inputs_embeds is not None:
            raise ValueError("You cannot specify both input_ids and inputs_embeds at the same time")
        elif input_ids is not None:
            batch_size, seq_length = input_ids.size()
        elif inputs_embeds is not None:
            batch_size, seq_length = inputs_embeds.size()[:-1]
        else:
            raise ValueError("You have to specify either input_ids or inputs_embeds")

        # construct attention mask if not given
        if attention_mask is None:
            attention_mask = torch.ones([batch_size, seq_length], dtype=torch.long, device=input_ids.device)

        # We add bos and eos input_ids in the modeling file instead of the tokenizer file to keep the logic simple
        # This logic is specific to ClvpConditioningEncoder and not used by other modules.
        input_ids, attention_mask = _pad_extra_bos_eos_tokens(
            input_ids,
            attention_mask,
            bos_token_id=self.text_config.bos_token_id,
            eos_token_id=self.text_config.eos_token_id,
        )

        inputs_embeds = self.text_token_embedding(input_ids)
        position_ids = attention_mask.cumsum(-1) - 1
        position_embeds = self.text_position_embedding(position_ids)
        text_embeds = inputs_embeds + position_embeds

        if self.gradient_checkpointing and self.training:
            # process each log-mel spectrogram into a single vector
            mel_spec = torch.utils.checkpoint.checkpoint(self.mel_conv, input_features)

            for i, mel_attn_block in enumerate(self.mel_attn_blocks):
                residual_mel_spec = mel_spec.transpose(1, 2)

                mel_spec = torch.utils.checkpoint.checkpoint(self.group_norms[i], mel_spec).transpose(1, 2)
                mel_spec = torch.utils.checkpoint.checkpoint(mel_attn_block, mel_spec)[0] + residual_mel_spec
                mel_spec = mel_spec.transpose(1, 2)

        else:
            # process each log-mel spectrogram into a single vector
            mel_spec = self.mel_conv(input_features)

            for i, mel_attn_block in enumerate(self.mel_attn_blocks):
                residual_mel_spec = mel_spec.transpose(1, 2)

                mel_spec = self.group_norms[i](mel_spec).transpose(1, 2)
                mel_spec = mel_attn_block(mel_spec)[0] + residual_mel_spec
                mel_spec = mel_spec.transpose(1, 2)

        mel_spec = mel_spec[:, :, 0]
        mel_spec = mel_spec.unsqueeze(1)

        # repeat if there is either (1 text vs N audios) or (N texts vs 1 audio)
        if text_embeds.shape[0] == 1 and mel_spec.shape[0] != 1:
            text_embeds = text_embeds.repeat(mel_spec.shape[0], 1, 1)
        elif text_embeds.shape[0] != 1 and mel_spec.shape[0] == 1:
            mel_spec = mel_spec.repeat(text_embeds.shape[0], 1, 1)
        # If there is N texts and M audios we will raise error since the number of text and audio must be same.
        elif text_embeds.shape[0] != mel_spec.shape[0]:
            raise ValueError(
                f"The number of texts and number of audios must be same. "
                f"Found {text_embeds.shape[0]} texts vs {mel_spec.shape[0]} audios"
            )

        return torch.concat([mel_spec, text_embeds], dim=1)