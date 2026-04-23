def export_prov2(
    gpt_path,
    vits_path,
    version,
    ref_audio_path,
    ref_text,
    output_path,
    export_bert_and_ssl=False,
    device="cpu",
    is_half=True,
):
    if sv_cn_model == None:
        init_sv_cn(device, is_half)

    if not os.path.exists(output_path):
        os.makedirs(output_path)
        print(f"目录已创建: {output_path}")
    else:
        print(f"目录已存在: {output_path}")

    ref_audio = torch.tensor([load_audio(ref_audio_path, 16000)]).float()
    ssl = SSLModel()
    if export_bert_and_ssl:
        s = ExportSSLModel(torch.jit.trace(ssl, example_inputs=(ref_audio)))
        ssl_path = os.path.join(output_path, "ssl_model.pt")
        torch.jit.script(s).save(ssl_path)
        print("#### exported ssl ####")
        export_bert(output_path)
    else:
        s = ExportSSLModel(ssl)

    print(f"device: {device}")

    ref_seq_id, ref_bert_T, ref_norm_text = get_phones_and_bert(ref_text, "all_zh", "v2")
    ref_seq = torch.LongTensor([ref_seq_id]).to(device)
    ref_bert = ref_bert_T.T
    if is_half:
        ref_bert = ref_bert.half()
    ref_bert = ref_bert.to(ref_seq.device)

    text_seq_id, text_bert_T, norm_text = get_phones_and_bert(
        "这是一个简单的示例，真没想到这么简单就完成了。The King and His Stories.Once there was a king. He likes to write stories, but his stories were not good. As people were afraid of him, they all said his stories were good.After reading them, the writer at once turned to the soldiers and said: Take me back to prison, please.",
        "auto",
        "v2",
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

    sv_model = ExportERes2NetV2(sv_cn_model)

    # vits_path = "SoVITS_weights_v2/xw_e8_s216.pth"
    vits = VitsModel(vits_path, version, is_half=is_half, device=device)
    vits.eval()

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
    t2s = torch.jit.script(t2s_m).to(device)
    print("#### script t2s_m ####")

    print("vits.hps.data.sampling_rate:", vits.hps.data.sampling_rate)
    gpt_sovits = GPT_SoVITS_V2Pro(t2s, vits, sv_model).to(device)
    gpt_sovits.eval()

    ref_audio_sr = s.resample(ref_audio, 16000, 32000)
    if is_half:
        ref_audio_sr = ref_audio_sr.half()
    ref_audio_sr = ref_audio_sr.to(device)

    torch._dynamo.mark_dynamic(ssl_content, 2)
    torch._dynamo.mark_dynamic(ref_audio_sr, 1)
    torch._dynamo.mark_dynamic(ref_seq, 1)
    torch._dynamo.mark_dynamic(text_seq, 1)
    torch._dynamo.mark_dynamic(ref_bert, 0)
    torch._dynamo.mark_dynamic(text_bert, 0)
    # torch._dynamo.mark_dynamic(sv_emb, 0)

    top_k = torch.LongTensor([5]).to(device)
    # 先跑一遍 sv_model 让它加载 cache，详情见 L880
    gpt_sovits.sv_model(ref_audio_sr)

    with torch.no_grad():
        gpt_sovits_export = torch.jit.trace(
            gpt_sovits,
            example_inputs=(
                ssl_content,
                ref_audio_sr,
                ref_seq,
                text_seq,
                ref_bert,
                text_bert,
                top_k,
            ),
        )

        gpt_sovits_path = os.path.join(output_path, "gpt_sovits_model.pt")
        gpt_sovits_export.save(gpt_sovits_path)
        print("#### exported gpt_sovits ####")
        audio = gpt_sovits_export(ssl_content, ref_audio_sr, ref_seq, text_seq, ref_bert, text_bert, top_k)
        print("start write wav")
        soundfile.write("out.wav", audio.float().detach().cpu().numpy(), 32000)