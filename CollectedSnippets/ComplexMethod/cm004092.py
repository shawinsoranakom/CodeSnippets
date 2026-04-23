def _get_input_mel(self, waveform: np.ndarray, max_length, truncation, padding) -> np.ndarray:
        """
        Extracts the mel spectrogram and prepares it for the mode based on the `truncation` and `padding` arguments.
        Four different path are possible:
            - `truncation="fusion"` and the length of the waveform is greater than the max length: the mel spectrogram
              will be computed on the entire audio. 3 random crops and a dowsampled version of the full mel spectrogram
              are then stacked together. They will later be used for `feature_fusion`.
            - `truncation="rand_trunc"` and the length of the waveform is smaller than the max length: the audio is
              padded based on `padding`.
            - `truncation="fusion"` and the length of the waveform is smaller than the max length: the audio is padded
              based on `padding`, and is repeated `4` times.
            - `truncation="rand_trunc"` and the length of the waveform is greater than the max length: the mel
              spectrogram will be computed on a random crop of the waveform.

        """
        if waveform.shape[0] > max_length:
            if truncation == "rand_trunc":
                longer = True
                # random crop to max_length (for compatibility) -> this should be handled by self.pad
                overflow = len(waveform) - max_length
                idx = np.random.randint(0, overflow + 1)
                waveform = waveform[idx : idx + max_length]
                input_mel = self._np_extract_fbank_features(waveform, self.mel_filters_slaney)[None, :]
            elif truncation == "fusion":
                mel = self._np_extract_fbank_features(waveform, self.mel_filters)
                chunk_frames = max_length // self.hop_length + 1  # the +1 related to how the spectrogram is computed
                total_frames = mel.shape[0]
                if chunk_frames == total_frames:
                    # there is a corner case where the audio length is larger than max_length but smaller than max_length+hop_length.
                    # In this case, we just use the whole audio.
                    input_mel = np.stack([mel, mel, mel, mel], axis=0)
                    longer = False
                else:
                    input_mel = self._random_mel_fusion(mel, total_frames, chunk_frames)
                    longer = True
            else:
                raise NotImplementedError(f"data_truncating {truncation} not implemented")

        else:
            longer = False
            # only use repeat as a new possible value for padding. you repeat the audio before applying the usual max_length padding
            if waveform.shape[0] < max_length:
                if padding == "repeat":
                    n_repeat = int(max_length / len(waveform))
                    waveform = np.tile(waveform, n_repeat + 1)[:max_length]
                if padding == "repeatpad":
                    n_repeat = int(max_length / len(waveform))
                    waveform = np.tile(waveform, n_repeat)
                waveform = np.pad(waveform, (0, max_length - waveform.shape[0]), mode="constant", constant_values=0)

            if truncation == "fusion":
                input_mel = self._np_extract_fbank_features(waveform, self.mel_filters)
                input_mel = np.stack([input_mel, input_mel, input_mel, input_mel], axis=0)
            else:
                input_mel = self._np_extract_fbank_features(waveform, self.mel_filters_slaney)[None, :]

        return input_mel, longer