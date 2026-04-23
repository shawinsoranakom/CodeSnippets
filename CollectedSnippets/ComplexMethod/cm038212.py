def get_audio_hidden_states(
        self, data: MiniCPMOAudioFeatureInputs
    ) -> list[torch.Tensor]:
        chunk_length = self.config.audio_chunk_length

        # (bs, 80, frames) or [], multi audios need filled in advance
        wavforms_raw = data["audio_features"]
        if isinstance(wavforms_raw, list):
            B = len(wavforms_raw)
            C = wavforms_raw[0].shape[-2]
            L = max(item.shape[-1] for item in wavforms_raw)
            device = wavforms_raw[0].device
            dtype = wavforms_raw[0].dtype

            wavforms = torch.zeros((B, C, L), dtype=dtype, device=device)
            for i, wavforms_item in enumerate(wavforms_raw):
                L_item = wavforms_item.shape[-1]
                wavforms[i, ..., :L_item] = wavforms_item
        else:
            wavforms = wavforms_raw

        # list, [[x1, x2], [y1], [z1]]
        audio_feature_lens_raw = data["audio_feature_lens"]
        if isinstance(audio_feature_lens_raw, torch.Tensor):
            audio_feature_lens_raw = audio_feature_lens_raw.unbind(0)

        audio_feature_lens = torch.hstack(audio_feature_lens_raw)
        batch_size, _, max_mel_seq_len = wavforms.shape
        max_seq_len = (max_mel_seq_len - 1) // 2 + 1

        # Create a sequence tensor of shape (batch_size, max_seq_len)
        seq_range = (
            torch.arange(
                0,
                max_seq_len,
                dtype=audio_feature_lens.dtype,
                device=audio_feature_lens.device,
            )
            .unsqueeze(0)
            .expand(batch_size, max_seq_len)
        )
        lengths_expand = audio_feature_lens.unsqueeze(1).expand(batch_size, max_seq_len)
        # Create mask
        padding_mask = seq_range >= lengths_expand  # 1 for padded values

        audio_attention_mask_ = padding_mask.view(batch_size, 1, 1, max_seq_len).expand(
            batch_size, 1, max_seq_len, max_seq_len
        )
        audio_attention_mask = audio_attention_mask_.to(
            dtype=self.apm.conv1.weight.dtype, device=self.apm.conv1.weight.device
        )

        if chunk_length > 0:
            chunk_num_frame = int(chunk_length * 50)
            chunk_mask = self.subsequent_chunk_mask(
                size=max_seq_len,
                chunk_size=chunk_num_frame,
                num_left_chunks=-1,
                device=audio_attention_mask_.device,
            )
            audio_attention_mask_ = torch.logical_or(
                audio_attention_mask_, torch.logical_not(chunk_mask)
            )

        audio_attention_mask[audio_attention_mask_] = float("-inf")
        audio_states = self.apm(
            wavforms, attention_mask=audio_attention_mask
        ).hidden_states[self.audio_encoder_layer]
        audio_embeds = self.audio_projection_layer(audio_states)

        audio_embeds = audio_embeds.transpose(1, 2)
        audio_embeds = self.audio_avg_pooler(audio_embeds)
        audio_embeds = audio_embeds.transpose(1, 2)

        _, feature_lens_after_pooling = self._get_feat_extract_output_lengths(
            audio_feature_lens
        )

        num_audio_tokens = feature_lens_after_pooling

        final_audio_embeds = list[torch.Tensor]()
        idx = 0
        for i in range(len(audio_feature_lens_raw)):
            target_audio_embeds_lst = list[torch.Tensor]()
            for _ in range(len(audio_feature_lens_raw[i])):
                target_audio_embeds_lst.append(
                    audio_embeds[idx, : num_audio_tokens[idx], :]
                )
                idx += 1

            final_audio_embeds.append(torch.cat(target_audio_embeds_lst))

        return final_audio_embeds