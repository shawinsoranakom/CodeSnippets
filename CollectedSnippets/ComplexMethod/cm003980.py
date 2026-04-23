def _extract_spectrogram(self, waveform: np.ndarray, attention_mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """"""
        if waveform.ndim == 1:  # If single waveform, add batch dimension
            waveform = np.expand_dims(waveform, axis=0)

        if self.dither > 0.0:
            waveform = waveform + self.dither * np.random.randn(*waveform.shape).astype(waveform.dtype)

        if self.input_scale_factor != 1.0:
            waveform = waveform * self.input_scale_factor

        # Semicausal time padding: prepend frame_length // 2 zeros so that the
        # first STFT frame is centered at t=0, matching sl.STFT(time_padding='semicausal').
        pad_left = self.frame_length // 2
        waveform = np.pad(waveform, ((0, 0), (pad_left, 0)), mode="constant")
        attention_mask = np.pad(attention_mask, (pad_left, 0), mode="constant", constant_values=0)

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

        # Apply window, then RFFT. np.fft.rfft with n=fft_length implicitly
        # right-pads frames to fft_length.
        frames = frames * self.window  # Broadcasting window
        stft = np.fft.rfft(frames, n=self.fft_length, axis=-1)

        magnitude_spec = np.abs(stft)

        mel_spec = np.matmul(magnitude_spec, self.mel_filters)
        log_mel_spec = np.log(mel_spec + self.mel_floor)

        if self.per_bin_mean is not None:
            log_mel_spec = log_mel_spec - self.per_bin_mean  # Broadcasting

        if self.per_bin_stddev is not None:
            log_mel_spec = log_mel_spec / self.per_bin_stddev  # Broadcasting

        mel_spectrogram = log_mel_spec.squeeze(0)
        num_mel_frames = mel_spectrogram.shape[0]

        # Build a frame-aware mask: a mel frame is valid only when every sample
        # in its analysis window [i*hop, i*hop + frame_size - 1] is real audio.
        # We check this by looking at the last sample of each frame's window.
        frame_end_indices = np.arange(num_mel_frames) * self.hop_length + frame_size_for_unfold - 1
        mask = attention_mask[frame_end_indices].astype(bool)
        return mel_spectrogram, mask