def get_sovits_weights(sovits_path):
    from config import pretrained_sovits_name

    path_sovits_v3 = pretrained_sovits_name["v3"]
    path_sovits_v4 = pretrained_sovits_name["v4"]
    is_exist_s2gv3 = os.path.exists(path_sovits_v3)
    is_exist_s2gv4 = os.path.exists(path_sovits_v4)

    version, model_version, if_lora_v3 = get_sovits_version_from_path_fast(sovits_path)
    is_exist = is_exist_s2gv3 if model_version == "v3" else is_exist_s2gv4
    path_sovits = path_sovits_v3 if model_version == "v3" else path_sovits_v4

    if if_lora_v3 == True and is_exist == False:
        logger.info("SoVITS %s 底模缺失，无法加载相应 LoRA 权重" % model_version)

    dict_s2 = load_sovits_new(sovits_path)
    hps = dict_s2["config"]
    hps = DictToAttrRecursive(hps)
    hps.model.semantic_frame_rate = "25hz"
    if "enc_p.text_embedding.weight" not in dict_s2["weight"]:
        hps.model.version = "v2"  # v3model,v2sybomls
    elif dict_s2["weight"]["enc_p.text_embedding.weight"].shape[0] == 322:
        hps.model.version = "v1"
    else:
        hps.model.version = "v2"

    model_params_dict = vars(hps.model)
    if model_version not in {"v3", "v4"}:
        if "Pro" in model_version:
            hps.model.version = model_version
            if sv_cn_model == None:
                init_sv_cn()

        vq_model = SynthesizerTrn(
            hps.data.filter_length // 2 + 1,
            hps.train.segment_size // hps.data.hop_length,
            n_speakers=hps.data.n_speakers,
            **model_params_dict,
        )
    else:
        hps.model.version = model_version
        vq_model = SynthesizerTrnV3(
            hps.data.filter_length // 2 + 1,
            hps.train.segment_size // hps.data.hop_length,
            n_speakers=hps.data.n_speakers,
            **model_params_dict,
        )
        if model_version == "v3":
            init_bigvgan()
        if model_version == "v4":
            init_hifigan()

    model_version = hps.model.version
    logger.info(f"模型版本: {model_version}")
    if "pretrained" not in sovits_path:
        try:
            del vq_model.enc_q
        except:
            pass
    if is_half == True:
        vq_model = vq_model.half().to(device)
    else:
        vq_model = vq_model.to(device)
    vq_model.eval()
    if if_lora_v3 == False:
        vq_model.load_state_dict(dict_s2["weight"], strict=False)
    else:
        path_sovits = path_sovits_v3 if model_version == "v3" else path_sovits_v4
        vq_model.load_state_dict(load_sovits_new(path_sovits)["weight"], strict=False)
        lora_rank = dict_s2["lora_rank"]
        lora_config = LoraConfig(
            target_modules=["to_k", "to_q", "to_v", "to_out.0"],
            r=lora_rank,
            lora_alpha=lora_rank,
            init_lora_weights=True,
        )
        vq_model.cfm = get_peft_model(vq_model.cfm, lora_config)
        vq_model.load_state_dict(dict_s2["weight"], strict=False)
        vq_model.cfm = vq_model.cfm.merge_and_unload()
        # torch.save(vq_model.state_dict(),"merge_win.pth")
        vq_model.eval()

    sovits = Sovits(vq_model, hps)
    return sovits