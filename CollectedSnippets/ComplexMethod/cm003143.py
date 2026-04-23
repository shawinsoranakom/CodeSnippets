def get_rt_detr_v2_config(model_name: str) -> RTDetrV2Config:
    config = RTDetrV2Config()

    config.num_labels = 80
    repo_id = "huggingface/label-files"
    filename = "coco-detection-mmdet-id2label.json"
    id2label = json.load(open(hf_hub_download(repo_id, filename, repo_type="dataset"), "r"))
    id2label = {int(k): v for k, v in id2label.items()}
    config.id2label = id2label
    config.label2id = {v: k for k, v in id2label.items()}

    if model_name == "rtdetr_v2_r18vd":
        config.backbone_config.hidden_sizes = [64, 128, 256, 512]
        config.backbone_config.depths = [2, 2, 2, 2]
        config.backbone_config.layer_type = "basic"
        config.encoder_in_channels = [128, 256, 512]
        config.hidden_expansion = 0.5
        config.decoder_layers = 3
    elif model_name == "rtdetr_v2_r34vd":
        config.backbone_config.hidden_sizes = [64, 128, 256, 512]
        config.backbone_config.depths = [3, 4, 6, 3]
        config.backbone_config.layer_type = "basic"
        config.encoder_in_channels = [128, 256, 512]
        config.hidden_expansion = 0.5
        config.decoder_layers = 4
    # TODO: check this not working
    elif model_name == "rtdetr_v2_r50vd_m":
        config.hidden_expansion = 0.5
    elif model_name == "rtdetr_v2_r50vd":
        pass
    elif model_name == "rtdetr_v2_r101vd":
        config.backbone_config.depths = [3, 4, 23, 3]
        config.encoder_ffn_dim = 2048
        config.encoder_hidden_dim = 384
        config.decoder_in_channels = [384, 384, 384]

    return config