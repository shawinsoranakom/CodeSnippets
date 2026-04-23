def get_weights_names():
    SoVITS_names = []
    for key in name2sovits_path:
        if os.path.exists(name2sovits_path[key]):
            SoVITS_names.append(key)
    for path in SoVITS_weight_root:
        if not os.path.exists(path):
            continue
        for name in os.listdir(path):
            if name.endswith(".pth"):
                SoVITS_names.append("%s/%s" % (path, name))
    if not SoVITS_names:
        SoVITS_names = [""]
    GPT_names = []
    for key in name2gpt_path:
        if os.path.exists(name2gpt_path[key]):
            GPT_names.append(key)
    for path in GPT_weight_root:
        if not os.path.exists(path):
            continue
        for name in os.listdir(path):
            if name.endswith(".ckpt"):
                GPT_names.append("%s/%s" % (path, name))
    SoVITS_names = sorted(SoVITS_names, key=custom_sort_key)
    GPT_names = sorted(GPT_names, key=custom_sort_key)
    if not GPT_names:
        GPT_names = [""]
    return SoVITS_names, GPT_names