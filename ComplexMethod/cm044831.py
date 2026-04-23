def __getitem__(self, index: int) -> Tuple[torch.Tensor, torch.Tensor, str, torch.Tensor]:
        try:
            filename = self.audio_files[index]

            # Use librosa.load that ensures loading waveform into mono with [-1, 1] float values
            # Audio is ndarray with shape [T_time]. Disable auto-resampling here to minimize overhead
            # The on-the-fly resampling during training will be done only for the obtained random chunk
            audio, source_sampling_rate = librosa.load(filename, sr=None, mono=True)

            # Main logic that uses <mel, audio> pair for training BigVGAN
            if not self.fine_tuning:
                if self.split:  # Training step
                    # Obtain randomized audio chunk
                    if source_sampling_rate != self.sampling_rate:
                        # Adjust segment size to crop if the source sr is different
                        target_segment_size = math.ceil(self.segment_size * (source_sampling_rate / self.sampling_rate))
                    else:
                        target_segment_size = self.segment_size

                    # Compute upper bound index for the random chunk
                    random_chunk_upper_bound = max(0, audio.shape[0] - target_segment_size)

                    # Crop or pad audio to obtain random chunk with target_segment_size
                    if audio.shape[0] >= target_segment_size:
                        audio_start = random.randint(0, random_chunk_upper_bound)
                        audio = audio[audio_start : audio_start + target_segment_size]
                    else:
                        audio = np.pad(
                            audio,
                            (0, target_segment_size - audio.shape[0]),
                            mode="constant",
                        )

                    # Resample audio chunk to self.sampling rate
                    if source_sampling_rate != self.sampling_rate:
                        audio = librosa.resample(
                            audio,
                            orig_sr=source_sampling_rate,
                            target_sr=self.sampling_rate,
                        )
                        if audio.shape[0] > self.segment_size:
                            # trim last elements to match self.segment_size (e.g., 16385 for 44khz downsampled to 24khz -> 16384)
                            audio = audio[: self.segment_size]

                else:  # Validation step
                    # Resample full audio clip to target sampling rate
                    if source_sampling_rate != self.sampling_rate:
                        audio = librosa.resample(
                            audio,
                            orig_sr=source_sampling_rate,
                            target_sr=self.sampling_rate,
                        )
                    # Trim last elements to match audio length to self.hop_size * n for evaluation
                    if (audio.shape[0] % self.hop_size) != 0:
                        audio = audio[: -(audio.shape[0] % self.hop_size)]

                # BigVGAN is trained using volume-normalized waveform
                audio = librosa.util.normalize(audio) * 0.95

                # Cast ndarray to torch tensor
                audio = torch.FloatTensor(audio)
                audio = audio.unsqueeze(0)  # [B(1), self.segment_size]

                # Compute mel spectrogram corresponding to audio
                mel = mel_spectrogram(
                    audio,
                    self.n_fft,
                    self.num_mels,
                    self.sampling_rate,
                    self.hop_size,
                    self.win_size,
                    self.fmin,
                    self.fmax,
                    center=False,
                )  # [B(1), self.num_mels, self.segment_size // self.hop_size]

            # Fine-tuning logic that uses pre-computed mel. Example: Using TTS model-generated mel as input
            else:
                # For fine-tuning, assert that the waveform is in the defined sampling_rate
                # Fine-tuning won't support on-the-fly resampling to be fool-proof (the dataset should have been prepared properly)
                assert source_sampling_rate == self.sampling_rate, (
                    f"For fine_tuning, waveform must be in the spcified sampling rate {self.sampling_rate}, got {source_sampling_rate}"
                )

                # Cast ndarray to torch tensor
                audio = torch.FloatTensor(audio)
                audio = audio.unsqueeze(0)  # [B(1), T_time]

                # Load pre-computed mel from disk
                mel = np.load(
                    os.path.join(
                        self.base_mels_path,
                        os.path.splitext(os.path.split(filename)[-1])[0] + ".npy",
                    )
                )
                mel = torch.from_numpy(mel)

                if len(mel.shape) < 3:
                    mel = mel.unsqueeze(0)  # ensure [B, C, T]

                if self.split:
                    frames_per_seg = math.ceil(self.segment_size / self.hop_size)

                    if audio.size(1) >= self.segment_size:
                        mel_start = random.randint(0, mel.size(2) - frames_per_seg - 1)
                        mel = mel[:, :, mel_start : mel_start + frames_per_seg]
                        audio = audio[
                            :,
                            mel_start * self.hop_size : (mel_start + frames_per_seg) * self.hop_size,
                        ]

                    # Pad pre-computed mel and audio to match length to ensuring fine-tuning without error.
                    # NOTE: this may introduce a single-frame misalignment of the <pre-computed mel, audio>
                    # To remove possible misalignment, it is recommended to prepare the <pre-computed mel, audio> pair where the audio length is the integer multiple of self.hop_size
                    mel = torch.nn.functional.pad(mel, (0, frames_per_seg - mel.size(2)), "constant")
                    audio = torch.nn.functional.pad(audio, (0, self.segment_size - audio.size(1)), "constant")

            # Compute mel_loss used by spectral regression objective. Uses self.fmax_loss instead (usually None)
            mel_loss = mel_spectrogram(
                audio,
                self.n_fft,
                self.num_mels,
                self.sampling_rate,
                self.hop_size,
                self.win_size,
                self.fmin,
                self.fmax_loss,
                center=False,
            )  # [B(1), self.num_mels, self.segment_size // self.hop_size]

            # Shape sanity checks
            assert (
                audio.shape[1] == mel.shape[2] * self.hop_size and audio.shape[1] == mel_loss.shape[2] * self.hop_size
            ), (
                f"Audio length must be mel frame length * hop_size. Got audio shape {audio.shape} mel shape {mel.shape} mel_loss shape {mel_loss.shape}"
            )

            return (mel.squeeze(), audio.squeeze(0), filename, mel_loss.squeeze())

        # If it encounters error during loading the data, skip this sample and load random other sample to the batch
        except Exception as e:
            if self.fine_tuning:
                raise e  # Terminate training if it is fine-tuning. The dataset should have been prepared properly.
            else:
                print(f"[WARNING] Failed to load waveform, skipping! filename: {filename} Error: {e}")
                return self[random.randrange(len(self))]