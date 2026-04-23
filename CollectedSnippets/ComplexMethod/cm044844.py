def using_vocoder_synthesis_batched_infer(
        self,
        idx_list: List[int],
        semantic_tokens_list: List[torch.Tensor],
        batch_phones: List[torch.Tensor],
        speed: float = 1.0,
        sample_steps: int = 32,
    ) -> List[torch.Tensor]:
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

        # #### batched inference
        overlapped_len = self.vocoder_configs["overlapped_len"]
        feat_chunks = []
        feat_lens = []
        feat_list = []

        for i, idx in enumerate(idx_list):
            phones = batch_phones[i].unsqueeze(0).to(self.configs.device)
            semantic_tokens = (
                semantic_tokens_list[i][-idx:].unsqueeze(0).unsqueeze(0)
            )  # .unsqueeze(0)#mq要多unsqueeze一次
            feat, _ = self.vits_model.decode_encp(semantic_tokens, phones, refer_audio_spec, ge, speed)
            feat_list.append(feat)
            feat_lens.append(feat.shape[2])

        feats = torch.cat(feat_list, 2)
        feats_padded = F.pad(feats, (overlapped_len, 0), "constant", 0)
        pos = 0
        padding_len = 0
        while True:
            if pos == 0:
                chunk = feats_padded[:, :, pos : pos + chunk_len]
            else:
                pos = pos - overlapped_len
                chunk = feats_padded[:, :, pos : pos + chunk_len]
            pos += chunk_len
            if chunk.shape[-1] == 0:
                break

            # padding for the last chunk
            padding_len = chunk_len - chunk.shape[2]
            if padding_len != 0:
                chunk = F.pad(chunk, (0, padding_len), "constant", 0)
            feat_chunks.append(chunk)

        feat_chunks = torch.cat(feat_chunks, 0)
        bs = feat_chunks.shape[0]
        fea_ref = fea_ref.repeat(bs, 1, 1)
        fea = torch.cat([fea_ref, feat_chunks], 2).transpose(2, 1)
        pred_spec = self.vits_model.cfm.inference(
            fea, torch.LongTensor([fea.size(1)]).to(fea.device), mel2, sample_steps, inference_cfg_rate=0
        )
        pred_spec = pred_spec[:, :, -chunk_len:]
        dd = pred_spec.shape[1]
        pred_spec = pred_spec.permute(1, 0, 2).contiguous().view(dd, -1).unsqueeze(0)
        # pred_spec = pred_spec[..., :-padding_len]

        pred_spec = denorm_spec(pred_spec)

        with torch.no_grad():
            wav_gen = self.vocoder(pred_spec)
            audio = wav_gen[0][0]  # .cpu().detach().numpy()

        audio_fragments = []
        upsample_rate = self.vocoder_configs["upsample_rate"]
        pos = 0

        while pos < audio.shape[-1]:
            audio_fragment = audio[pos : pos + chunk_len * upsample_rate]
            audio_fragments.append(audio_fragment)
            pos += chunk_len * upsample_rate

        audio = self.sola_algorithm(audio_fragments, overlapped_len * upsample_rate)
        if padding_len > 0:
            audio = audio[overlapped_len * upsample_rate : -padding_len * upsample_rate]
        else:
            audio = audio[overlapped_len * upsample_rate :]

        audio_fragments = []
        for feat_len in feat_lens:
            audio_fragment = audio[: feat_len * upsample_rate]
            audio_fragments.append(audio_fragment)
            audio = audio[feat_len * upsample_rate :]

        return audio_fragments