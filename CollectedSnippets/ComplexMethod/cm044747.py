def get_tts_wav(
    ref_wav_path,
    prompt_text,
    prompt_language,
    text,
    text_language,
    top_k=15,
    top_p=0.6,
    temperature=0.6,
    speed=1,
    inp_refs=None,
    sample_steps=32,
    if_sr=False,
    spk="default",
):
    infer_sovits = speaker_list[spk].sovits
    vq_model = infer_sovits.vq_model
    hps = infer_sovits.hps
    version = vq_model.version

    infer_gpt = speaker_list[spk].gpt
    t2s_model = infer_gpt.t2s_model
    max_sec = infer_gpt.max_sec

    if version == "v3":
        if sample_steps not in [4, 8, 16, 32, 64, 128]:
            sample_steps = 32
    elif version == "v4":
        if sample_steps not in [4, 8, 16, 32]:
            sample_steps = 8

    if if_sr and version != "v3":
        if_sr = False

    t0 = ttime()
    prompt_text = prompt_text.strip("\n")
    if prompt_text[-1] not in splits:
        prompt_text += "。" if prompt_language != "en" else "."
    prompt_language, text = prompt_language, text.strip("\n")
    dtype = torch.float16 if is_half == True else torch.float32
    zero_wav = np.zeros(int(hps.data.sampling_rate * 0.3), dtype=np.float16 if is_half == True else np.float32)
    with torch.no_grad():
        wav16k, sr = librosa.load(ref_wav_path, sr=16000)
        wav16k = torch.from_numpy(wav16k)
        zero_wav_torch = torch.from_numpy(zero_wav)
        if is_half == True:
            wav16k = wav16k.half().to(device)
            zero_wav_torch = zero_wav_torch.half().to(device)
        else:
            wav16k = wav16k.to(device)
            zero_wav_torch = zero_wav_torch.to(device)
        wav16k = torch.cat([wav16k, zero_wav_torch])
        ssl_content = ssl_model.model(wav16k.unsqueeze(0))["last_hidden_state"].transpose(1, 2)  # .float()
        codes = vq_model.extract_latent(ssl_content)
        prompt_semantic = codes[0, 0]
        prompt = prompt_semantic.unsqueeze(0).to(device)

        is_v2pro = version in {"v2Pro", "v2ProPlus"}
        if version not in {"v3", "v4"}:
            refers = []
            if is_v2pro:
                sv_emb = []
                if sv_cn_model == None:
                    init_sv_cn()
            if inp_refs:
                for path in inp_refs:
                    try:  #####这里加上提取sv的逻辑，要么一堆sv一堆refer，要么单个sv单个refer
                        refer, audio_tensor = get_spepc(hps, path.name, dtype, device, is_v2pro)
                        refers.append(refer)
                        if is_v2pro:
                            sv_emb.append(sv_cn_model.compute_embedding3(audio_tensor))
                    except Exception as e:
                        logger.error(e)
            if len(refers) == 0:
                refers, audio_tensor = get_spepc(hps, ref_wav_path, dtype, device, is_v2pro)
                refers = [refers]
                if is_v2pro:
                    sv_emb = [sv_cn_model.compute_embedding3(audio_tensor)]
        else:
            refer, audio_tensor = get_spepc(hps, ref_wav_path, dtype, device)

    t1 = ttime()
    # os.environ['version'] = version
    prompt_language = dict_language[prompt_language.lower()]
    text_language = dict_language[text_language.lower()]
    phones1, bert1, norm_text1 = get_phones_and_bert(prompt_text, prompt_language, version)
    texts = text.split("\n")
    audio_bytes = BytesIO()

    for text in texts:
        # 简单防止纯符号引发参考音频泄露
        if only_punc(text):
            continue

        audio_opt = []
        if text[-1] not in splits:
            text += "。" if text_language != "en" else "."
        phones2, bert2, norm_text2 = get_phones_and_bert(text, text_language, version)
        bert = torch.cat([bert1, bert2], 1)

        all_phoneme_ids = torch.LongTensor(phones1 + phones2).to(device).unsqueeze(0)
        bert = bert.to(device).unsqueeze(0)
        all_phoneme_len = torch.tensor([all_phoneme_ids.shape[-1]]).to(device)
        t2 = ttime()
        with torch.no_grad():
            pred_semantic, idx = t2s_model.model.infer_panel(
                all_phoneme_ids,
                all_phoneme_len,
                prompt,
                bert,
                # prompt_phone_len=ph_offset,
                top_k=top_k,
                top_p=top_p,
                temperature=temperature,
                early_stop_num=hz * max_sec,
            )
            pred_semantic = pred_semantic[:, -idx:].unsqueeze(0)
        t3 = ttime()

        if version not in {"v3", "v4"}:
            if is_v2pro:
                audio = (
                    vq_model.decode(
                        pred_semantic,
                        torch.LongTensor(phones2).to(device).unsqueeze(0),
                        refers,
                        speed=speed,
                        sv_emb=sv_emb,
                    )
                    .detach()
                    .cpu()
                    .numpy()[0, 0]
                )
            else:
                audio = (
                    vq_model.decode(
                        pred_semantic, torch.LongTensor(phones2).to(device).unsqueeze(0), refers, speed=speed
                    )
                    .detach()
                    .cpu()
                    .numpy()[0, 0]
                )
        else:
            phoneme_ids0 = torch.LongTensor(phones1).to(device).unsqueeze(0)
            phoneme_ids1 = torch.LongTensor(phones2).to(device).unsqueeze(0)

            fea_ref, ge = vq_model.decode_encp(prompt.unsqueeze(0), phoneme_ids0, refer)
            ref_audio, sr = torchaudio.load(ref_wav_path)
            ref_audio = ref_audio.to(device).float()
            if ref_audio.shape[0] == 2:
                ref_audio = ref_audio.mean(0).unsqueeze(0)

            tgt_sr = 24000 if version == "v3" else 32000
            if sr != tgt_sr:
                ref_audio = resample(ref_audio, sr, tgt_sr, device)
            mel2 = mel_fn(ref_audio) if version == "v3" else mel_fn_v4(ref_audio)
            mel2 = norm_spec(mel2)
            T_min = min(mel2.shape[2], fea_ref.shape[2])
            mel2 = mel2[:, :, :T_min]
            fea_ref = fea_ref[:, :, :T_min]
            Tref = 468 if version == "v3" else 500
            Tchunk = 934 if version == "v3" else 1000
            if T_min > Tref:
                mel2 = mel2[:, :, -Tref:]
                fea_ref = fea_ref[:, :, -Tref:]
                T_min = Tref
            chunk_len = Tchunk - T_min
            mel2 = mel2.to(dtype)
            fea_todo, ge = vq_model.decode_encp(pred_semantic, phoneme_ids1, refer, ge, speed)
            cfm_resss = []
            idx = 0
            while 1:
                fea_todo_chunk = fea_todo[:, :, idx : idx + chunk_len]
                if fea_todo_chunk.shape[-1] == 0:
                    break
                idx += chunk_len
                fea = torch.cat([fea_ref, fea_todo_chunk], 2).transpose(2, 1)
                cfm_res = vq_model.cfm.inference(
                    fea, torch.LongTensor([fea.size(1)]).to(fea.device), mel2, sample_steps, inference_cfg_rate=0
                )
                cfm_res = cfm_res[:, :, mel2.shape[2] :]
                mel2 = cfm_res[:, :, -T_min:]
                fea_ref = fea_todo_chunk[:, :, -T_min:]
                cfm_resss.append(cfm_res)
            cfm_res = torch.cat(cfm_resss, 2)
            cfm_res = denorm_spec(cfm_res)
            if version == "v3":
                if bigvgan_model == None:
                    init_bigvgan()
            else:  # v4
                if hifigan_model == None:
                    init_hifigan()
            vocoder_model = bigvgan_model if version == "v3" else hifigan_model
            with torch.inference_mode():
                wav_gen = vocoder_model(cfm_res)
                audio = wav_gen[0][0].cpu().detach().numpy()

        max_audio = np.abs(audio).max()
        if max_audio > 1:
            audio /= max_audio
        audio_opt.append(audio)
        audio_opt.append(zero_wav)
        audio_opt = np.concatenate(audio_opt, 0)
        t4 = ttime()

        if version in {"v1", "v2", "v2Pro", "v2ProPlus"}:
            sr = 32000
        elif version == "v3":
            sr = 24000
        else:
            sr = 48000  # v4

        if if_sr and sr == 24000:
            audio_opt = torch.from_numpy(audio_opt).float().to(device)
            audio_opt, sr = audio_sr(audio_opt.unsqueeze(0), sr)
            max_audio = np.abs(audio_opt).max()
            if max_audio > 1:
                audio_opt /= max_audio
            sr = 48000

        if is_int32:
            audio_bytes = pack_audio(audio_bytes, (audio_opt * 2147483647).astype(np.int32), sr)
        else:
            audio_bytes = pack_audio(audio_bytes, (audio_opt * 32768).astype(np.int16), sr)
        # logger.info("%.3f\t%.3f\t%.3f\t%.3f" % (t1 - t0, t2 - t1, t3 - t2, t4 - t3))
        if stream_mode == "normal":
            audio_bytes, audio_chunk = read_clean_buffer(audio_bytes)
            yield audio_chunk

    if not stream_mode == "normal":
        if media_type == "wav":
            if version in {"v1", "v2", "v2Pro", "v2ProPlus"}:
                sr = 32000
            elif version == "v3":
                sr = 48000 if if_sr else 24000
            else:
                sr = 48000  # v4
            audio_bytes = pack_wav(audio_bytes, sr)
        yield audio_bytes.getvalue()