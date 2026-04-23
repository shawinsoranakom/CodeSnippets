def export_1(ref_wav_path, ref_wav_text, version="v3"):
    if version == "v3":
        sovits = get_sovits_weights("GPT_SoVITS/pretrained_models/s2Gv3.pth")
        init_bigvgan()
    else:
        sovits = get_sovits_weights("GPT_SoVITS/pretrained_models/gsv-v4-pretrained/s2Gv4.pth")
        init_hifigan()

    dict_s1 = torch.load("GPT_SoVITS/pretrained_models/s1v3.ckpt")
    raw_t2s = get_raw_t2s_model(dict_s1).to(device)
    print("#### get_raw_t2s_model ####")
    print(raw_t2s.config)

    if is_half:
        raw_t2s = raw_t2s.half().to(device)

    t2s_m = T2SModel(raw_t2s)
    t2s_m.eval()
    script_t2s = torch.jit.script(t2s_m).to(device)

    hps = sovits.hps
    # ref_wav_path = "onnx/ad/ref.wav"
    speed = 1.0
    sample_steps = 8
    dtype = torch.float16 if is_half == True else torch.float32
    refer = get_spepc(hps, ref_wav_path).to(device).to(dtype)
    zero_wav = np.zeros(
        int(hps.data.sampling_rate * 0.3),
        dtype=np.float16 if is_half == True else np.float32,
    )

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
        codes = sovits.vq_model.extract_latent(ssl_content)
        prompt_semantic = codes[0, 0]
        prompt = prompt_semantic.unsqueeze(0).to(device)

    # phones1, bert1, norm_text1 = get_phones_and_bert(
    #     "你这老坏蛋，我找了你这么久，真没想到在这里找到你。他说。", "all_zh", "v3"
    # )
    phones1, bert1, norm_text1 = get_phones_and_bert(ref_wav_text, "auto", "v3")
    phones2, bert2, norm_text2 = get_phones_and_bert(
        "这是一个简单的示例，真没想到这么简单就完成了。The King and His Stories.Once there was a king. He likes to write stories, but his stories were not good. As people were afraid of him, they all said his stories were good.After reading them, the writer at once turned to the soldiers and said: Take me back to prison, please.",
        "auto",
        "v3",
    )
    phoneme_ids0 = torch.LongTensor(phones1).to(device).unsqueeze(0)
    phoneme_ids1 = torch.LongTensor(phones2).to(device).unsqueeze(0)

    # codes = sovits.vq_model.extract_latent(ssl_content)
    # prompt_semantic = codes[0, 0]
    # prompts = prompt_semantic.unsqueeze(0)

    top_k = torch.LongTensor([15]).to(device)
    print("topk", top_k)

    bert1 = bert1.T.to(device)
    bert2 = bert2.T.to(device)
    print(
        prompt.dtype,
        phoneme_ids0.dtype,
        phoneme_ids1.dtype,
        bert1.dtype,
        bert2.dtype,
        top_k.dtype,
    )
    print(
        prompt.shape,
        phoneme_ids0.shape,
        phoneme_ids1.shape,
        bert1.shape,
        bert2.shape,
        top_k.shape,
    )
    pred_semantic = t2s_m(prompt, phoneme_ids0, phoneme_ids1, bert1, bert2, top_k)

    ge = sovits.vq_model.create_ge(refer)
    prompt_ = prompt.unsqueeze(0)

    torch._dynamo.mark_dynamic(prompt_, 2)
    torch._dynamo.mark_dynamic(phoneme_ids0, 1)

    fea_ref = sovits.vq_model(prompt_, phoneme_ids0, ge)

    inputs = {
        "forward": (prompt_, phoneme_ids0, ge),
        "extract_latent": ssl_content,
        "create_ge": refer,
    }

    trace_vq_model = torch.jit.trace_module(sovits.vq_model, inputs, optimize=True)
    trace_vq_model.save("onnx/ad/vq_model.pt")

    print(fea_ref.shape, fea_ref.dtype, ge.shape)
    print(prompt_.shape, phoneme_ids0.shape, ge.shape)

    # vq_model = torch.jit.trace(
    #     sovits.vq_model,
    #     optimize=True,
    #     # strict=False,
    #     example_inputs=(prompt_, phoneme_ids0, ge),
    # )
    # vq_model = sovits.vq_model
    vq_model = trace_vq_model

    if version == "v3":
        gpt_sovits_half = ExportGPTSovitsHalf(sovits.hps, script_t2s, trace_vq_model)
        torch.jit.script(gpt_sovits_half).save("onnx/ad/gpt_sovits_v3_half.pt")
    else:
        gpt_sovits_half = ExportGPTSovitsV4Half(sovits.hps, script_t2s, trace_vq_model)
        torch.jit.script(gpt_sovits_half).save("onnx/ad/gpt_sovits_v4_half.pt")

    ref_audio, sr = torchaudio.load(ref_wav_path)
    ref_audio = ref_audio.to(device).float()
    if ref_audio.shape[0] == 2:
        ref_audio = ref_audio.mean(0).unsqueeze(0)
    tgt_sr = 24000 if version == "v3" else 32000
    if sr != tgt_sr:
        ref_audio = resample(ref_audio, sr, tgt_sr)
    # mel2 = mel_fn(ref_audio)
    mel2 = mel_fn(ref_audio) if version == "v3" else mel_fn_v4(ref_audio)
    mel2 = norm_spec(mel2)
    T_min = min(mel2.shape[2], fea_ref.shape[2])
    fea_ref = fea_ref[:, :, :T_min]
    print("fea_ref:", fea_ref.shape, T_min)
    Tref = 468 if version == "v3" else 500
    Tchunk = 934 if version == "v3" else 1000
    if T_min > Tref:
        mel2 = mel2[:, :, -Tref:]
        fea_ref = fea_ref[:, :, -Tref:]
        T_min = Tref
    chunk_len = Tchunk - T_min
    mel2 = mel2.to(dtype)

    # fea_todo, ge = sovits.vq_model(pred_semantic,y_lengths, phoneme_ids1, ge)
    fea_todo = vq_model(pred_semantic, phoneme_ids1, ge)

    cfm_resss = []
    idx = 0
    sample_steps = torch.LongTensor([sample_steps]).to(device)
    export_cfm_ = ExportCFM(sovits.cfm)
    while 1:
        print("idx:", idx)
        fea_todo_chunk = fea_todo[:, :, idx : idx + chunk_len]
        if fea_todo_chunk.shape[-1] == 0:
            break

        print(
            "export_cfm:",
            fea_ref.shape,
            fea_todo_chunk.shape,
            mel2.shape,
            sample_steps.shape,
        )
        if idx == 0:
            fea = torch.cat([fea_ref, fea_todo_chunk], 2).transpose(2, 1)
            export_cfm_ = export_cfm(
                export_cfm_,
                fea,
                torch.LongTensor([fea.size(1)]).to(fea.device),
                mel2,
                sample_steps,
            )
            # torch.onnx.export(
            #     export_cfm_,
            #     (
            #         fea_ref,
            #         fea_todo_chunk,
            #         mel2,
            #         sample_steps,
            #     ),
            #     "onnx/ad/cfm.onnx",
            #     input_names=["fea_ref", "fea_todo_chunk", "mel2", "sample_steps"],
            #     output_names=["cfm_res", "fea_ref_", "mel2_"],
            #     dynamic_axes={
            #         "fea_ref": [2],
            #         "fea_todo_chunk": [2],
            #         "mel2": [2],
            #     },
            # )

        idx += chunk_len

        cfm_res, fea_ref, mel2 = export_cfm_(fea_ref, fea_todo_chunk, mel2, sample_steps)
        cfm_resss.append(cfm_res)
        continue

    cmf_res = torch.cat(cfm_resss, 2)
    cmf_res = denorm_spec(cmf_res).to(device)
    print("cmf_res:", cmf_res.shape, cmf_res.dtype)
    with torch.inference_mode():
        cmf_res_rand = torch.randn(1, 100, 934).to(device).to(dtype)
        torch._dynamo.mark_dynamic(cmf_res_rand, 2)
        if version == "v3":
            bigvgan_model_ = torch.jit.trace(bigvgan_model, optimize=True, example_inputs=(cmf_res_rand,))
            bigvgan_model_.save("onnx/ad/bigvgan_model.pt")
            wav_gen = bigvgan_model(cmf_res)
        else:
            hifigan_model_ = torch.jit.trace(hifigan_model, optimize=True, example_inputs=(cmf_res_rand,))
            hifigan_model_.save("onnx/ad/hifigan_model.pt")
            wav_gen = hifigan_model(cmf_res)

        print("wav_gen:", wav_gen.shape, wav_gen.dtype)
        audio = wav_gen[0][0].cpu().detach().numpy()

    sr = 24000 if version == "v3" else 48000
    soundfile.write("out.export.wav", (audio * 32768).astype(np.int16), sr)