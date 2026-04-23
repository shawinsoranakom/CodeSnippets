def _extract_spectrogram(self, waveform: np.ndarray, attention_mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """"""
        if waveform.ndim == 1:  # If single waveform, add batch dimension
            waveform = np.expand_dims(waveform, axis=0)

        if self.dither > 0.0:
            waveform = waveform + self.dither * np.random.randn(*waveform.shape).astype(waveform.dtype)

        if self.input_scale_factor != 1.0:
            waveform = waveform * self.input_scale_factor

        frame_size_for_unfold = self.frame_length + 1

        # NumPy equivalent of unfold for [B, NumFrames, frame_size_for_unfold]
        frames_to_process = _unfold(waveform, dimension=-1, size=frame_size_for_unfold, step=self.hop_length)

        if self.preemphasis > 0.0:
            if self.preemphasis_htk_flavor:
                first_in_frame = frames_to_process[..., :1] * (1.0 - self.preemphasis)
                rest_in_frame = frames_to_process[..., 1:-1] - self.preemphasis * frames_to_process[..., :-2]
                frames = np.concatenate([first_in_frame, rest_in_frame], axis=-1)
            else:
                frames = frames_to_process[..., 1:] - self.preemphasis * frames_to_process[..., :-1]
        else:
            frames = frames_to_process[..., :-1]

        frames = frames * self.window  # Broadcasting window
        stft = np.fft.rfft(frames, n=self.fft_length, axis=-1)

        magnitude_spec = np.abs(stft)

        mel_spec = np.matmul(magnitude_spec, self.mel_filters)
        log_mel_spec = np.log(np.maximum(mel_spec, self.mel_floor))

        if self.per_bin_mean is not None:
            log_mel_spec = log_mel_spec - self.per_bin_mean  # Broadcasting

        if self.per_bin_stddev is not None:
            log_mel_spec = log_mel_spec / self.per_bin_stddev  # Broadcasting

        mel_spectrogram = log_mel_spec.squeeze(0)
        mask = attention_mask[:: self.hop_length].astype(bool)
        # TODO: The filtered mask is always exactly 3 elements longer than the mel_spectrogram. Why???
        return mel_spectrogram, mask[: mel_spectrogram.shape[0]]