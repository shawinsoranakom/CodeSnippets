def get_swinv2_config(swinv2_name):
    config = Swinv2Config()
    name_split = swinv2_name.split("_")

    model_size = name_split[1]
    if "to" in name_split[3]:
        img_size = int(name_split[3][-3:])
    else:
        img_size = int(name_split[3])
    if "to" in name_split[2]:
        window_size = int(name_split[2][-2:])
    else:
        window_size = int(name_split[2][6:])

    if model_size == "tiny":
        embed_dim = 96
        depths = (2, 2, 6, 2)
        num_heads = (3, 6, 12, 24)
    elif model_size == "small":
        embed_dim = 96
        depths = (2, 2, 18, 2)
        num_heads = (3, 6, 12, 24)
    elif model_size == "base":
        embed_dim = 128
        depths = (2, 2, 18, 2)
        num_heads = (4, 8, 16, 32)
    else:
        embed_dim = 192
        depths = (2, 2, 18, 2)
        num_heads = (6, 12, 24, 48)

    if "to" in swinv2_name:
        config.pretrained_window_sizes = (12, 12, 12, 6)

    if ("22k" in swinv2_name) and ("to" not in swinv2_name):
        num_classes = 21841
        repo_id = "huggingface/label-files"
        filename = "imagenet-22k-id2label.json"
        id2label = json.load(open(hf_hub_download(repo_id, filename, repo_type="dataset"), "r"))
        id2label = {int(k): v for k, v in id2label.items()}
        config.id2label = id2label
        config.label2id = {v: k for k, v in id2label.items()}

    else:
        num_classes = 1000
        repo_id = "huggingface/label-files"
        filename = "imagenet-1k-id2label.json"
        id2label = json.load(open(hf_hub_download(repo_id, filename, repo_type="dataset"), "r"))
        id2label = {int(k): v for k, v in id2label.items()}
        config.id2label = id2label
        config.label2id = {v: k for k, v in id2label.items()}

    config.image_size = img_size
    config.num_labels = num_classes
    config.embed_dim = embed_dim
    config.depths = depths
    config.num_heads = num_heads
    config.window_size = window_size

    return config