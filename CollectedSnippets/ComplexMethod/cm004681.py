def __call__(
        self,
        audio: np.ndarray | list[float] | list[np.ndarray] | list[list[float]],
        sampling_rate: int | list[int],
        steps_per_beat: int = 2,
        resample: bool | None = True,
        return_attention_mask: bool | None = False,
        return_tensors: str | TensorType | None = None,
        **kwargs,
    ) -> BatchFeature:
        """
        Main method to featurize and prepare for the model.

        Args:
            audio (`np.ndarray`, `List`):
                The audio or batch of audio to be processed. Each audio can be a numpy array, a list of float values, a
                list of numpy arrays or a list of list of float values.
            sampling_rate (`int`):
                The sampling rate at which the `audio` input was sampled. It is strongly recommended to pass
                `sampling_rate` at the forward call to prevent silent errors.
            steps_per_beat (`int`, *optional*, defaults to 2):
                This is used in interpolating `beat_times`.
            resample (`bool`, *optional*, defaults to `True`):
                Determines whether to resample the audio to `sampling_rate` or not before processing. Must be True
                during inference.
            return_attention_mask (`bool` *optional*, defaults to `False`):
                Denotes if attention_mask for input_features, beatsteps and extrapolated_beatstep will be given as
                output or not. Automatically set to True for batched inputs.
            return_tensors (`str` or [`~utils.TensorType`], *optional*):
                If set, will return tensors instead of list of python integers. Acceptable values are:
                - `'pt'`: Return PyTorch `torch.Tensor` objects.
                - `'np'`: Return Numpy `np.ndarray` objects.
                If nothing is specified, it will return list of `np.ndarray` arrays.
        """

        requires_backends(self, ["librosa"])
        is_batched = isinstance(audio, (list, tuple)) and isinstance(audio[0], (np.ndarray, tuple, list))
        if is_batched:
            # This enables the user to process files of different sampling_rate at same time
            if not isinstance(sampling_rate, list):
                raise ValueError(
                    "Please give sampling_rate of each audio separately when you are passing multiple raw_audios at the same time. "
                    f"Received {sampling_rate}, expected [audio_1_sr, ..., audio_n_sr]."
                )
            return_attention_mask = True if return_attention_mask is None else return_attention_mask
        else:
            audio = [audio]
            sampling_rate = [sampling_rate]
            return_attention_mask = False if return_attention_mask is None else return_attention_mask

        batch_input_features, batch_beatsteps, batch_ext_beatstep = [], [], []
        for single_raw_audio, single_sampling_rate in zip(audio, sampling_rate):
            bpm, beat_times, confidence, estimates, essentia_beat_intervals = self.extract_rhythm(
                audio=single_raw_audio
            )
            beatsteps = self.interpolate_beat_times(beat_times=beat_times, steps_per_beat=steps_per_beat, n_extend=1)

            if self.sampling_rate != single_sampling_rate and self.sampling_rate is not None:
                if resample:
                    # Change sampling_rate to self.sampling_rate
                    single_raw_audio = librosa.core.resample(
                        single_raw_audio,
                        orig_sr=single_sampling_rate,
                        target_sr=self.sampling_rate,
                        res_type="kaiser_best",
                    )
                else:
                    warnings.warn(
                        f"The sampling_rate of the provided audio is different from the target sampling_rate "
                        f"of the Feature Extractor, {self.sampling_rate} vs {single_sampling_rate}. "
                        f"In these cases it is recommended to use `resample=True` in the `__call__` method to "
                        f"get the optimal behaviour."
                    )

            single_sampling_rate = self.sampling_rate
            start_sample = int(beatsteps[0] * single_sampling_rate)
            end_sample = int(beatsteps[-1] * single_sampling_rate)

            input_features, extrapolated_beatstep = self.preprocess_mel(
                single_raw_audio[start_sample:end_sample], beatsteps - beatsteps[0]
            )

            mel_specs = self.mel_spectrogram(input_features.astype(np.float32))

            # apply np.log to get log mel-spectrograms
            log_mel_specs = np.log(np.clip(mel_specs, a_min=1e-6, a_max=None))

            input_features = np.transpose(log_mel_specs, (0, -1, -2))

            batch_input_features.append(input_features)
            batch_beatsteps.append(beatsteps)
            batch_ext_beatstep.append(extrapolated_beatstep)

        output = BatchFeature(
            {
                "input_features": batch_input_features,
                "beatsteps": batch_beatsteps,
                "extrapolated_beatstep": batch_ext_beatstep,
            }
        )

        output = self.pad(
            output,
            is_batched=is_batched,
            return_attention_mask=return_attention_mask,
            return_tensors=return_tensors,
        )

        return output