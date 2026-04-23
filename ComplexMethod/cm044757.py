def change_sovits_weights(sovits_path, prompt_language=None, text_language=None):
    if "！" in sovits_path or "!" in sovits_path:
        sovits_path = name2sovits_path[sovits_path]
    global version, model_version, dict_language, if_lora_v3
    version, model_version, if_lora_v3 = get_sovits_version_from_path_fast(sovits_path)
    # print(sovits_path,version, model_version, if_lora_v3)
    is_exist = is_exist_s2gv3 if model_version == "v3" else is_exist_s2gv4
    path_sovits = path_sovits_v3 if model_version == "v3" else path_sovits_v4
    if if_lora_v3 == True and is_exist == False:
        info = path_sovits + "SoVITS %s" % model_version + i18n("底模缺失，无法加载相应 LoRA 权重")
        gr.Warning(info)
        raise FileExistsError(info)
    dict_language = dict_language_v1 if version == "v1" else dict_language_v2
    if prompt_language is not None and text_language is not None:
        if prompt_language in list(dict_language.keys()):
            prompt_text_update, prompt_language_update = (
                {"__type__": "update"},
                {"__type__": "update", "value": prompt_language},
            )
        else:
            prompt_text_update = {"__type__": "update", "value": ""}
            prompt_language_update = {"__type__": "update", "value": i18n("中文")}
        if text_language in list(dict_language.keys()):
            text_update, text_language_update = {"__type__": "update"}, {"__type__": "update", "value": text_language}
        else:
            text_update = {"__type__": "update", "value": ""}
            text_language_update = {"__type__": "update", "value": i18n("中文")}
        if model_version in v3v4set:
            visible_sample_steps = True
            visible_inp_refs = False
        else:
            visible_sample_steps = False
            visible_inp_refs = True
        yield (
            {"__type__": "update", "choices": list(dict_language.keys())},
            {"__type__": "update", "choices": list(dict_language.keys())},
            prompt_text_update,
            prompt_language_update,
            text_update,
            text_language_update,
            {"__type__": "update", "interactive": visible_sample_steps, "value": 32},
            {"__type__": "update", "visible": visible_inp_refs},
            {"__type__": "update", "interactive": True if model_version not in v3v4set else False},
            {"__type__": "update", "value": i18n("模型加载中，请等待"), "interactive": False},
        )

    tts_pipeline.init_vits_weights(sovits_path)
    yield (
        {"__type__": "update", "choices": list(dict_language.keys())},
        {"__type__": "update", "choices": list(dict_language.keys())},
        prompt_text_update,
        prompt_language_update,
        text_update,
        text_language_update,
        {"__type__": "update", "interactive": visible_sample_steps, "value": 32},
        {"__type__": "update", "visible": visible_inp_refs},
        {"__type__": "update", "interactive": True if model_version not in v3v4set else False},
        {"__type__": "update", "value": i18n("合成语音"), "interactive": True},
    )
    with open("./weight.json") as f:
        data = f.read()
        data = json.loads(data)
        data["SoVITS"][version] = sovits_path
    with open("./weight.json", "w") as f:
        f.write(json.dumps(data))