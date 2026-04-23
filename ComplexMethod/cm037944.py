def get_audio_features(
        self,
        input_embeds: torch.Tensor,
        audio_attention_mask: torch.Tensor | None = None,
        audio_projection_mode: str = "speech",
    ) -> torch.Tensor:
        """
        arguments:
            input_embeds: audio features (B, T, D)  B: num audios in a sequence
        """
        if self.freeze_audio_processor:
            with torch.no_grad():
                audio_features, masks = self.encoder(input_embeds, audio_attention_mask)
        else:
            audio_features, masks = self.encoder(input_embeds, audio_attention_mask)

        if self.qformer is not None:
            audio_features, _ = self.qformer(audio_features, mask=None)

        if self.conv_ds is not None:
            if masks is not None:
                masks = masks.squeeze(1)

            audio_features, masks = self.conv_ds(audio_features, mask=masks)

        if self.linear_downsample_rate != 1:
            bs, seq_len, feat_dim = audio_features.size()
            padding = seq_len % self.linear_downsample_rate
            if padding > 0:
                audio_features = F.pad(
                    audio_features,
                    (0, 0, 0, self.linear_downsample_rate - padding),
                    "constant",
                    0,
                )

            seq_len = audio_features.size(1)
            audio_features = audio_features.view(
                bs,
                seq_len // self.linear_downsample_rate,
                feat_dim * self.linear_downsample_rate,
            )

        if audio_projection_mode == "speech":
            audio_set_tensor = self.audio_projection(audio_features)
        elif audio_projection_mode == "vision":
            audio_set_tensor = self.audio_projection_for_vision(audio_features)
        else:
            raise ValueError(
                f"audio_projection_mode = {audio_projection_mode} not implemented"
            )

        return audio_set_tensor