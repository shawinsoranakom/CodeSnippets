def _parse_audio_data(
        self,
        data: ModalityData[AudioItem],
    ) -> ModalityDataItems[Any, Any] | None:
        if data is None:
            return None

        if self.is_embeddings(data):
            return AudioEmbeddingItems(data, self.expected_hidden_size)

        data_items: list[AudioItem]
        if (
            (is_list_of(data, float) and len(data) > 0)
            or (isinstance(data, (np.ndarray, torch.Tensor)) and data.ndim == 1)
            or isinstance(data, tuple)
        ):
            data_items = [data]
        elif isinstance(data, (np.ndarray, torch.Tensor)):
            data_items = [elem for elem in data]
        else:
            data_items = data  # type: ignore[assignment]

        new_audios = list[np.ndarray]()
        for data_item in data_items:
            audio, orig_sr = self._get_audio_with_sr(data_item)
            if orig_sr is None:
                new_audio = audio
            else:
                new_audio = self.audio_resampler.resample(audio, orig_sr=orig_sr)

            # Apply channel normalization if target_channels is set
            if self.target_channels is not None:
                spec = AudioSpec(target_channels=self.target_channels)
                new_audio = normalize_audio(new_audio, spec)

            new_audios.append(new_audio)

        return AudioProcessorItems(new_audios)