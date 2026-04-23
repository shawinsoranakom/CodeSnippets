def test_stream(
    gpt_path,
    vits_path,
    version,
    ref_audio_path,
    ref_text,
    output_path,
    device="cpu",
    is_half=True,
):
    if export_torch_script.sv_cn_model == None:
        init_sv_cn(device,is_half)

    ref_audio = torch.tensor([load_audio(ref_audio_path, 16000)]).float()
    ssl = SSLModel()

    print(f"device: {device}")

    ref_seq_id, ref_bert_T, ref_norm_text = get_phones_and_bert(
        ref_text, "all_zh", "v2"
    )
    ref_seq = torch.LongTensor([ref_seq_id]).to(device)
    ref_bert = ref_bert_T.T
    if is_half:
        ref_bert = ref_bert.half()
    ref_bert = ref_bert.to(ref_seq.device)

    text_seq_id, text_bert_T, norm_text = get_phones_and_bert(
        "这是一个简单的示例，真没想到这么简单就完成了，真的神奇，接下来我们说说狐狸,可能这就是狐狸吧.它有长长的尾巴，尖尖的耳朵，传说中还有九条尾巴。你觉得狐狸神奇吗？", "auto", "v2"
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
    if is_half:
        ref_audio_sr = ref_audio_sr.half()
    ref_audio_sr = ref_audio_sr.to(device)

    top_k = 15

    codes = vits.vq_model.extract_latent(ssl_content)
    prompt_semantic = codes[0, 0]
    prompts = prompt_semantic.unsqueeze(0)

    audio_16k = resamplex(ref_audio_sr, 32000, 16000).to(ref_audio_sr.dtype)
    sv_emb = sv_model(audio_16k)
    print("text_seq",text_seq.shape)

    refer = spectrogram_torch(
        vits.hann_window,
        ref_audio_sr,
        vits.hps.data.filter_length,
        vits.hps.data.sampling_rate,
        vits.hps.data.hop_length,
        vits.hps.data.win_length,
        center=False,
    )

    st = time.time()
    et = time.time()

    y_len, y, xy_pos, k_cache, v_cache = stream_t2s.pre_infer(prompts, ref_seq, text_seq, ref_bert, text_bert, top_k)
    idx = 1
    last_idx = 0
    audios = []
    raw_audios = []
    last_audio_ret = None
    offset_index = []
    full_audios = []
    print("y.shape:", y.shape)
    cut_id = 0
    while True:
        y, xy_pos, last_token, k_cache, v_cache = stream_t2s(idx, top_k, y_len, y, xy_pos, k_cache, v_cache)
        # print("y.shape:", y.shape)
        stop = last_token==t2s.EOS
        print('idx:',idx , 'y.shape:', y.shape, y.shape[1]-idx)

        if last_token < 50 and idx-last_idx > (len(audios)+1) * 25 and idx > cut_id:
            cut_id = idx + 7
            print('trigger:',idx, last_idx, y[:,-idx+last_idx:], y[:,-idx+last_idx:].shape)
            # y = torch.cat([y, y[:,-1:]], dim=1)
            # idx+=1

        if stop :
            idx -=1
            print('stop')
            print(idx, y[:,-idx+last_idx:])
            print(idx,last_idx, y.shape)
            print(y[:,-idx:-idx+20])


        # 玄学这档子事说不清楚
        if idx == cut_id or stop:
            print(f"idx: {idx}, last_idx: {last_idx}, cut_id: {cut_id}, stop: {stop}")
            audio = vits.vq_model(y[:,-idx:].unsqueeze(0), text_seq, refer, speed=1.0, sv_emb=sv_emb)[0, 0]
            full_audios.append(audio)
            if last_idx == 0:
                last_audio_ret = audio[-1280*8:-1280*8+256]
                audio = audio[:-1280*8]
                raw_audios.append(audio)
                et = time.time()
            else:
                if stop:
                    audio_ = audio[last_idx*1280 -1280*8:]
                    raw_audios.append(audio_)
                    i, x = find_best_audio_offset_fast(last_audio_ret, audio_[:1280])
                    offset_index.append(i)
                    audio = audio_[i:]
                else:
                    audio_ = audio[last_idx*1280 -1280*8:-1280*8]
                    raw_audios.append(audio_)
                    i, x = find_best_audio_offset_fast(last_audio_ret, audio_[:1280])
                    offset_index.append(i)
                    last_audio_ret = audio[-1280*8:-1280*8+256]
                    audio = audio_[i:]
            last_idx = idx
            # print(f'write {output_path}/out_{audio_index}')
            # soundfile.write(f"{output_path}/out_{audio_index}.wav", audio.float().detach().cpu().numpy(), 32000)
            audios.append(audio)
        # print(idx,'/',1500 , y.shape, y[0,-1].item(), stop)
        if idx>1500:
            break

        if stop:
            break

        idx+=1

    at = time.time()

    for (i,a) in enumerate(audios):
        print(f'write {output_path}/out_{i}')
        soundfile.write(f"{output_path}/out_{i}.wav", a.float().detach().cpu().numpy(), 32000)

    print(f"frist token: {et - st:.4f} seconds")
    print(f"all token: {at - st:.4f} seconds")
    audio = vits.vq_model(y[:,-idx:].unsqueeze(0), text_seq, refer, speed=1.0, sv_emb=sv_emb)[0, 0]
    soundfile.write(f"{output_path}/out_final.wav", audio.float().detach().cpu().numpy(), 32000)
    audio = torch.cat(audios, dim=0)
    soundfile.write(f"{output_path}/out.wav", audio.float().detach().cpu().numpy(), 32000)
    audio_raw = torch.cat(raw_audios, dim=0)
    soundfile.write(f"{output_path}/out.raw.wav", audio_raw.float().detach().cpu().numpy(), 32000)


    colors = ['red', 'green', 'blue', 'orange', 'purple', 'cyan', 'magenta', 'yellow']

    max_duration = full_audios[-1].shape[0]
    plt.xlim(0, max_duration)

    last_line = 0

    for i,a in enumerate(full_audios):
        plt.plot((a+2.0*i).float().detach().cpu().numpy(), color=colors[i], alpha=0.5, label=f"Audio {i}")
        # plt.axvline(x=last_line, color=colors[i], linestyle='--')
        last_line = a.shape[0]-8*1280
        plt.axvline(x=last_line, color=colors[i], linestyle='--')

    plt.plot((audio-2.0).float().detach().cpu().numpy(), color='black', label='Final Audio')

    plt.plot((audio_raw-4.0).float().detach().cpu().numpy(), color='cyan', label='Raw Audio')

    print("offset_index:", offset_index)
    plt.show()