def forward(
        self,
        input_features: torch.Tensor,
        feature_lens: torch.Tensor,
        aftercnn_lens: torch.Tensor,
        speech_maxlen: int,
        **kwargs: object,
    ) -> BaseModelOutput:
        # For max-length audio (300s => ~7500 speech frames at 25Hz), the
        # Torch SDPA path can be prohibitively memory hungry (~O(n^2) inside the
        # longest chunks). Require FlashAttention for such inputs to avoid OOM
        # and performance cliffs.
        if int(speech_maxlen) >= 7500:
            if not _has_module("flash_attn"):
                raise RuntimeError(
                    "FunAudioChat long audio (~300s) requires FlashAttention-2 "
                    "for the continuous audio tower, but `flash_attn` is not "
                    "installed in the runtime environment."
                )
            if not getattr(
                self.layers[0].self_attn.attn, "is_flash_attn_backend", False
            ):
                raise RuntimeError(
                    "FunAudioChat long audio (~300s) requires FlashAttention for the "
                    "continuous audio tower, but the selected MM encoder attention "
                    "backend is not FlashAttention."
                )

        # Handle empty / invalid items (feature_lens == 0) without crashing.
        original_batch_size = int(feature_lens.size(0))
        device = input_features.device

        valid_mask = feature_lens > 0
        valid_indices = torch.where(valid_mask)[0]

        if valid_indices.numel() == 0:
            output_dim = int(self.proj.out_features)
            return BaseModelOutput(
                last_hidden_state=torch.zeros(
                    (original_batch_size, speech_maxlen, output_dim),
                    device=device,
                    dtype=self.proj.weight.dtype,
                )
            )

        input_features_list = input_features.split(feature_lens.tolist(), dim=1)
        valid_input_features_list = [input_features_list[int(i)] for i in valid_indices]
        valid_input_features = torch.cat(valid_input_features_list, dim=1)

        valid_feature_lens = feature_lens[valid_mask]
        valid_aftercnn_lens = aftercnn_lens[valid_mask]

        chunk_num = torch.ceil(valid_feature_lens / (self.n_window * 2)).long()

        chunk_lengths_list: list[int] = []
        full_chunk_len = self.n_window * 2
        for i, length in enumerate(valid_feature_lens):
            num_chunks_for_sample = int(chunk_num[i].item())
            if num_chunks_for_sample == 0:
                continue
            chunk_lengths_list.extend([full_chunk_len] * (num_chunks_for_sample - 1))
            last_chunk_len = int(length.item()) % full_chunk_len
            if last_chunk_len == 0:
                last_chunk_len = full_chunk_len
            chunk_lengths_list.append(last_chunk_len)

        chunk_lengths = torch.tensor(
            chunk_lengths_list, dtype=torch.long, device=device
        )

        chunk_list = valid_input_features.split(chunk_lengths.tolist(), dim=1)
        padded_feature, padded_mask, padded_mask_after_cnn = (
            self.padded_and_mask_function(
                chunk_list, chunk_lengths, padding_value=0, padding_side="right"
            )
        )

        padded_embed = nn.functional.gelu(self.conv1(padded_feature)) * padded_mask
        padded_embed = nn.functional.gelu(self.conv2(padded_embed)).transpose(1, 2)

        padded_embed = padded_embed + self.positional_embedding.positional_embedding[
            : padded_embed.shape[1], :
        ].unsqueeze(0).to(padded_embed.dtype)

        hidden_states = padded_embed[padded_mask_after_cnn]
        cu_seqlens = torch.cat(
            (
                torch.zeros(1, device=padded_mask_after_cnn.device, dtype=torch.int32),
                padded_mask_after_cnn.sum(1).cumsum(0),
            )
        ).to(torch.int32)

        for encoder_layer in self.layers:
            (hidden_states,) = encoder_layer(
                hidden_states,
                cu_seqlens=cu_seqlens,
                **kwargs,
            )

        hidden_states_list = hidden_states.split(valid_aftercnn_lens.tolist(), dim=0)

        pooled_list: list[torch.Tensor] = []
        pooled_lengths: list[int] = []
        for each_audio_states in hidden_states_list:
            seq_len = int(each_audio_states.shape[0])
            if seq_len >= 2:
                pooled = nn.functional.avg_pool1d(
                    each_audio_states.transpose(0, 1), kernel_size=2, stride=2
                ).transpose(0, 1)
            else:
                pooled = each_audio_states
            pooled_list.append(pooled)
            pooled_lengths.append(int(pooled.shape[0]))

        pooled_concat = torch.cat(pooled_list, dim=0)
        processed_concat = self.proj(self.ln_post(pooled_concat))
        processed_audio_list = list(processed_concat.split(pooled_lengths, dim=0))

        output_dim = (
            int(processed_audio_list[0].shape[-1])
            if processed_audio_list
            else int(self.proj.out_features)
        )
        output_hidden_states = torch.zeros(
            (original_batch_size, speech_maxlen, output_dim),
            dtype=processed_audio_list[0].dtype
            if processed_audio_list
            else self.proj.weight.dtype,
            device=device,
        )

        for valid_idx, processed in zip(valid_indices, processed_audio_list):
            seq_len = min(int(processed.shape[0]), int(speech_maxlen))
            output_hidden_states[int(valid_idx), :seq_len] = processed[:seq_len]

        return BaseModelOutput(last_hidden_state=output_hidden_states)