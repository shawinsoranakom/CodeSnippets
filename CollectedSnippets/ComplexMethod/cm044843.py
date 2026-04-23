def using_vocoder_synthesis(
        self, semantic_tokens: torch.Tensor, phones: torch.Tensor, speed: float = 1.0, sample_steps: int = 32
    ):
        prompt_semantic_tokens = self.prompt_cache["prompt_semantic"].unsqueeze(0).unsqueeze(0).to(self.configs.device)
        prompt_phones = torch.LongTensor(self.prompt_cache["phones"]).unsqueeze(0).to(self.configs.device)
        raw_entry = self.prompt_cache["refer_spec"][0]
        if isinstance(raw_entry, tuple):
            raw_entry = raw_entry[0]
        refer_audio_spec = raw_entry.to(dtype=self.precision, device=self.configs.device)

        fea_ref, ge = self.vits_model.decode_encp(prompt_semantic_tokens, prompt_phones, refer_audio_spec)
        ref_audio: torch.Tensor = self.prompt_cache["raw_audio"]
        ref_sr = self.prompt_cache["raw_sr"]
        ref_audio = ref_audio.to(self.configs.device).float()
        if ref_audio.shape[0] == 2:
            ref_audio = ref_audio.mean(0).unsqueeze(0)

        # tgt_sr = self.vocoder_configs["sr"]
        tgt_sr = 24000 if self.configs.version == "v3" else 32000
        if ref_sr != tgt_sr:
            ref_audio = resample(ref_audio, ref_sr, tgt_sr, self.configs.device)

        mel2 = mel_fn(ref_audio) if self.configs.version == "v3" else mel_fn_v4(ref_audio)
        mel2 = norm_spec(mel2)
        T_min = min(mel2.shape[2], fea_ref.shape[2])
        mel2 = mel2[:, :, :T_min]
        fea_ref = fea_ref[:, :, :T_min]
        T_ref = self.vocoder_configs["T_ref"]
        T_chunk = self.vocoder_configs["T_chunk"]
        if T_min > T_ref:
            mel2 = mel2[:, :, -T_ref:]
            fea_ref = fea_ref[:, :, -T_ref:]
            T_min = T_ref
        chunk_len = T_chunk - T_min

        mel2 = mel2.to(self.precision)
        fea_todo, ge = self.vits_model.decode_encp(semantic_tokens, phones, refer_audio_spec, ge, speed)

        cfm_resss = []
        idx = 0
        while 1:
            fea_todo_chunk = fea_todo[:, :, idx : idx + chunk_len]
            if fea_todo_chunk.shape[-1] == 0:
                break
            idx += chunk_len
            fea = torch.cat([fea_ref, fea_todo_chunk], 2).transpose(2, 1)

            cfm_res = self.vits_model.cfm.inference(
                fea, torch.LongTensor([fea.size(1)]).to(fea.device), mel2, sample_steps, inference_cfg_rate=0
            )
            cfm_res = cfm_res[:, :, mel2.shape[2] :]

            mel2 = cfm_res[:, :, -T_min:]
            fea_ref = fea_todo_chunk[:, :, -T_min:]

            cfm_resss.append(cfm_res)
        cfm_res = torch.cat(cfm_resss, 2)
        cfm_res = denorm_spec(cfm_res)

        with torch.inference_mode():
            wav_gen = self.vocoder(cfm_res)
            audio = wav_gen[0][0]  # .cpu().detach().numpy()

        return audio