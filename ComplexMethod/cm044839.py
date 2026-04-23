def _get_ref_spec(self, ref_audio_path):
        raw_audio, raw_sr = torchaudio.load(ref_audio_path)
        raw_audio = raw_audio.to(self.configs.device).float()
        self.prompt_cache["raw_audio"] = raw_audio
        self.prompt_cache["raw_sr"] = raw_sr

        if raw_sr != self.configs.sampling_rate:
            audio = raw_audio.to(self.configs.device)
            if audio.shape[0] == 2:
                audio = audio.mean(0).unsqueeze(0)
            audio = resample(audio, raw_sr, self.configs.sampling_rate, self.configs.device)
        else:
            audio = raw_audio.to(self.configs.device)
            if audio.shape[0] == 2:
                audio = audio.mean(0).unsqueeze(0)

        maxx = audio.abs().max()
        if maxx > 1:
            audio /= min(2, maxx)
        spec = spectrogram_torch(
            audio,
            self.configs.filter_length,
            self.configs.sampling_rate,
            self.configs.hop_length,
            self.configs.win_length,
            center=False,
        )
        if self.configs.is_half:
            spec = spec.half()
        if self.is_v2pro == True:
            audio = resample(audio, self.configs.sampling_rate, 16000, self.configs.device)
            if self.configs.is_half:
                audio = audio.half()
        else:
            audio = None
        return spec, audio