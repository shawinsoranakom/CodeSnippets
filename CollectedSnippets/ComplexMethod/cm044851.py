def check_details(path_list=None, is_train=False, is_dataset_processing=False):
    if is_dataset_processing:
        list_path, audio_path = path_list
        if not list_path.endswith(".list"):
            gr.Warning(i18n("请填入正确的List路径"))
            return
        if audio_path:
            if not os.path.isdir(audio_path):
                gr.Warning(i18n("请填入正确的音频文件夹路径"))
                return
        with open(list_path, "r", encoding="utf8") as f:
            line = f.readline().strip("\n").split("\n")
        wav_name, _, __, ___ = line[0].split("|")
        wav_name = clean_path(wav_name)
        if audio_path != "" and audio_path != None:
            wav_name = os.path.basename(wav_name)
            wav_path = "%s/%s" % (audio_path, wav_name)
        else:
            wav_path = wav_name
        if os.path.exists(wav_path):
            ...
        else:
            gr.Warning(wav_path + i18n("路径错误"))
        return
    if is_train:
        path_list.append(os.path.join(path_list[0], "2-name2text.txt"))
        path_list.append(os.path.join(path_list[0], "4-cnhubert"))
        path_list.append(os.path.join(path_list[0], "5-wav32k"))
        path_list.append(os.path.join(path_list[0], "6-name2semantic.tsv"))
        phone_path, hubert_path, wav_path, semantic_path = path_list[1:]
        with open(phone_path, "r", encoding="utf-8") as f:
            if f.read(1):
                ...
            else:
                gr.Warning(i18n("缺少音素数据集"))
        if os.listdir(hubert_path):
            ...
        else:
            gr.Warning(i18n("缺少Hubert数据集"))
        if os.listdir(wav_path):
            ...
        else:
            gr.Warning(i18n("缺少音频数据集"))
        df = pd.read_csv(semantic_path, delimiter="\t", encoding="utf-8")
        if len(df) >= 1:
            ...
        else:
            gr.Warning(i18n("缺少语义数据集"))