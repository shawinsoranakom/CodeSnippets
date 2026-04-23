def export_prov2(
    gpt_path,
    vits_path,
    version,
    ref_audio_path,
    ref_text,
    output_path,
    device="cpu",
    is_half=True,
    lang="auto",
):
    if export_torch_script.sv_cn_model == None:
        init_sv_cn(device,is_half)

    ref_audio = torch.tensor([load_audio(ref_audio_path, 16000)]).float()
    ssl = SSLModel()

    print(f"device: {device}")

    ref_seq_id, ref_bert_T, ref_norm_text = get_phones_and_bert(
        ref_text, lang, "v2"
    )
    ref_seq = torch.LongTensor([ref_seq_id]).to(device)
    ref_bert = ref_bert_T.T
    if is_half:
        ref_bert = ref_bert.half()
    ref_bert = ref_bert.to(ref_seq.device)

    text_seq_id, text_bert_T, norm_text = get_phones_and_bert(
        "这是一个简单的示例，真没想到这么简单就完成了.The King and His Stories.Once there was a king.He likes to write stories, but his stories were not good.", "auto", "v2"
    )
    text_seq = torch.LongTensor([text_seq_id]).to(device)
    text_bert = text_bert_T.T
    if is_half:
        text_bert = text_bert.half()
    text_bert = text_bert.to(text_seq.device)

    ssl_content = ssl(ref_audio)
    if is_half:
        ssl_content = ssl_content.half()
    ssl_content = ssl_content.to(device)

    sv_model = ExportERes2NetV2(export_torch_script.sv_cn_model)

    # vits_path = "SoVITS_weights_v2/xw_e8_s216.pth"
    vits = VitsModel(vits_path, version,is_half=is_half,device=device)
    vits.eval()
    vits = StepVitsModel(vits, sv_model)

    # gpt_path = "GPT_weights_v2/xw-e15.ckpt"
    # dict_s1 = torch.load(gpt_path, map_location=device)
    dict_s1 = torch.load(gpt_path, weights_only=False)
    raw_t2s = get_raw_t2s_model(dict_s1).to(device)
    print("#### get_raw_t2s_model ####")
    print(raw_t2s.config)
    if is_half:
        raw_t2s = raw_t2s.half()
    t2s_m = T2SModel(raw_t2s)
    t2s_m.eval()
    # t2s = torch.jit.script(t2s_m).to(device)
    t2s = t2s_m
    print("#### script t2s_m ####")

    print("vits.hps.data.sampling_rate:", vits.hps.data.sampling_rate)

    stream_t2s = StreamT2SModel(t2s).to(device)
    stream_t2s = torch.jit.script(stream_t2s)

    ref_audio_sr = resamplex(ref_audio, 16000, 32000)
    ref_audio_sr = ref_audio_sr.to(device)
    if is_half:
        ref_audio_sr = ref_audio_sr.half()

    top_k = 15

    prompts = vits.extract_latent(ssl_content)

    audio_16k = resamplex(ref_audio_sr, 32000, 16000).to(ref_audio_sr.dtype)
    sv_emb = sv_model(audio_16k)
    print("text_seq",text_seq.shape)
    # torch.jit.trace()

    refer,sv_emb = vits.ref_handle(ref_audio_sr)

    st = time.time()
    et = time.time()

    y_len, y, xy_pos, k_cache, v_cache = stream_t2s.pre_infer(prompts, ref_seq, text_seq, ref_bert, text_bert, top_k)
    idx = 1
    print("y.shape:", y.shape)
    while True:
        y, xy_pos, last_token, k_cache, v_cache = stream_t2s(idx, top_k, y_len, y, xy_pos, k_cache, v_cache)
        # print("y.shape:", y.shape)

        idx+=1
        # print(idx,'/',1500 , y.shape, y[0,-1].item(), stop)
        if idx>1500:
            break

        if last_token == t2s.EOS:
            break

    at = time.time()
    print("EOS:",t2s.EOS)

    print(f"frist token: {et - st:.4f} seconds")
    print(f"all token: {at - st:.4f} seconds")
    print("sv_emb", sv_emb.shape)
    print("refer",refer.shape)
    y = y[:,-idx:].unsqueeze(0)
    print("y", y.shape)
    audio = vits(y, text_seq, refer, sv_emb)
    soundfile.write(f"{output_path}/out_final.wav", audio.float().detach().cpu().numpy(), 32000)

    torch._dynamo.mark_dynamic(ssl_content, 2)
    torch._dynamo.mark_dynamic(ref_audio_sr, 1)
    torch._dynamo.mark_dynamic(ref_seq, 1)
    torch._dynamo.mark_dynamic(text_seq, 1)
    torch._dynamo.mark_dynamic(ref_bert, 0)
    torch._dynamo.mark_dynamic(text_bert, 0)
    torch._dynamo.mark_dynamic(refer, 2)
    torch._dynamo.mark_dynamic(y, 2)

    inputs = {
        "forward": (y, text_seq, refer, sv_emb),
        "extract_latent": ssl_content,
        "ref_handle": ref_audio_sr,
    }

    stream_t2s.save(f"{output_path}/t2s.pt")
    torch.jit.trace_module(vits, inputs=inputs, optimize=True).save(f"{output_path}/vits.pt")
    torch.jit.script(find_best_audio_offset_fast, optimize=True).save(f"{output_path}/find_best_audio_offset_fast.pt")