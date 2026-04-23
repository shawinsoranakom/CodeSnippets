def audio_postprocess(
        self,
        audio: List[torch.Tensor],
        sr: int,
        batch_index_list: list = None,
        speed_factor: float = 1.0,
        split_bucket: bool = True,
        fragment_interval: float = 0.3,
        super_sampling: bool = False,
    ) -> Tuple[int, np.ndarray]:
        if fragment_interval>0:
            zero_wav = torch.zeros(
                int(self.configs.sampling_rate * fragment_interval), dtype=self.precision, device=self.configs.device
            )

        for i, batch in enumerate(audio):
            for j, audio_fragment in enumerate(batch):
                max_audio = torch.abs(audio_fragment).max()  # 简单防止16bit爆音
                if max_audio > 1:
                    audio_fragment /= max_audio
                audio_fragment: torch.Tensor = torch.cat([audio_fragment, zero_wav], dim=0) if fragment_interval>0 else audio_fragment
                audio[i][j] = audio_fragment

        if split_bucket:
            audio = self.recovery_order(audio, batch_index_list)
        else:
            # audio = [item for batch in audio for item in batch]
            audio = sum(audio, [])

        audio = torch.cat(audio, dim=0)

        if super_sampling:
            print(f"############ {i18n('音频超采样')} ############")
            t1 = time.perf_counter()
            self.init_sr_model()
            if not self.sr_model_not_exist:
                audio, sr = self.sr_model(audio.unsqueeze(0), sr)
                max_audio = np.abs(audio).max()
                if max_audio > 1:
                    audio /= max_audio
                audio = (audio * 32768).astype(np.int16)
            else:
                audio = audio.cpu().numpy()
                audio = (audio * 32768).astype(np.int16)
            t2 = time.perf_counter()
            print(f"超采样用时：{t2 - t1:.3f}s")
        else:
            audio = audio.cpu().numpy()
            audio = (audio * 32768).astype(np.int16)


        # try:
        #     if speed_factor != 1.0:
        #         audio = speed_change(audio, speed=speed_factor, sr=int(sr))
        # except Exception as e:
        #     print(f"Failed to change speed of audio: \n{e}")

        return sr, audio