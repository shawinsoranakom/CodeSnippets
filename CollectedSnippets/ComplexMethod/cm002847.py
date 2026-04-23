def get_d_fine_config(model_name: str) -> DFineConfig:
    config = DFineConfig()

    config.num_labels = 80
    repo_id = "huggingface/label-files"
    filename = "object365-id2label.json" if "obj365" in model_name else "coco-detection-mmdet-id2label.json"
    id2label = json.load(open(hf_hub_download(repo_id, filename, repo_type="dataset"), "r"))
    id2label = {int(k): v for k, v in id2label.items()}
    config.id2label = id2label
    config.label2id = {v: k for k, v in id2label.items()}

    config.backbone_config.hidden_sizes = [64, 128, 256, 512]
    config.backbone_config.layer_type = "basic"
    config.backbone_config.embedding_size = 32
    config.hidden_expansion = 1.0
    config.decoder_layers = 6

    if model_name in ["dfine_x_coco", "dfine_x_obj2coco", "dfine_x_obj365"]:
        config.backbone_config.hidden_sizes = [256, 512, 1024, 2048]
        config.backbone_config.stage_in_channels = [64, 128, 512, 1024]
        config.backbone_config.stage_mid_channels = [64, 128, 256, 512]
        config.backbone_config.stage_out_channels = [128, 512, 1024, 2048]
        config.backbone_config.stage_num_blocks = [1, 2, 5, 2]
        config.backbone_config.stage_downsample = [False, True, True, True]
        config.backbone_config.stage_light_block = [False, False, True, True]
        config.backbone_config.stage_kernel_size = [3, 3, 5, 5]
        config.backbone_config.stage_numb_of_layers = [6, 6, 6, 6]
        config.backbone_config.stem_channels = [3, 32, 64]
        config.encoder_in_channels = [512, 1024, 2048]
        config.encoder_hidden_dim = 384
        config.encoder_ffn_dim = 2048
        config.decoder_n_points = [3, 6, 3]
        config.decoder_in_channels = [384, 384, 384]
        if model_name == "dfine_x_obj365":
            config.num_labels = 366
    elif model_name in ["dfine_m_coco", "dfine_m_obj2coco", "dfine_m_obj365"]:
        config.backbone_config.hidden_sizes = [192, 384, 768, 1536]
        config.backbone_config.stem_channels = [3, 24, 32]
        config.backbone_config.stage_in_channels = [32, 96, 384, 768]
        config.backbone_config.stage_mid_channels = [32, 64, 128, 256]
        config.backbone_config.stage_out_channels = [96, 384, 768, 1536]
        config.backbone_config.stage_num_blocks = [1, 1, 3, 1]
        config.backbone_config.stage_downsample = [False, True, True, True]
        config.backbone_config.stage_light_block = [False, False, True, True]
        config.backbone_config.stage_kernel_size = [3, 3, 5, 5]
        config.backbone_config.stage_numb_of_layers = [4, 4, 4, 4]
        config.decoder_layers = 4
        config.decoder_n_points = [3, 6, 3]
        config.encoder_in_channels = [384, 768, 1536]
        config.backbone_config.use_learnable_affine_block = True
        config.depth_mult = 0.67
        if model_name == "dfine_m_obj365":
            config.num_labels = 366
    elif model_name in ["dfine_l_coco", "dfine_l_obj2coco_e25", "dfine_l_obj365"]:
        config.backbone_config.hidden_sizes = [256, 512, 1024, 2048]
        config.backbone_config.stem_channels = [3, 32, 48]
        config.backbone_config.stage_in_channels = [48, 128, 512, 1024]
        config.backbone_config.stage_mid_channels = [48, 96, 192, 384]
        config.backbone_config.stage_out_channels = [128, 512, 1024, 2048]
        config.backbone_config.stage_num_blocks = [1, 1, 3, 1]
        config.backbone_config.stage_downsample = [False, True, True, True]
        config.backbone_config.stage_light_block = [False, False, True, True]
        config.backbone_config.stage_kernel_size = [3, 3, 5, 5]
        config.backbone_config.stage_numb_of_layers = [6, 6, 6, 6]
        config.encoder_ffn_dim = 1024
        config.encoder_in_channels = [512, 1024, 2048]
        config.decoder_n_points = [3, 6, 3]
        if model_name == "dfine_l_obj365":
            config.num_labels = 366
    elif model_name in ["dfine_n_coco", "dfine_n_obj2coco_e25", "dfine_n_obj365"]:
        config.backbone_config.hidden_sizes = [128, 256, 512, 1024]
        config.backbone_config.stem_channels = [3, 16, 16]
        config.backbone_config.stage_in_channels = [16, 64, 256, 512]
        config.backbone_config.stage_mid_channels = [16, 32, 64, 128]
        config.backbone_config.stage_out_channels = [64, 256, 512, 1024]
        config.backbone_config.stage_num_blocks = [1, 1, 2, 1]
        config.backbone_config.stage_downsample = [False, True, True, True]
        config.backbone_config.stage_light_block = [False, False, True, True]
        config.backbone_config.stage_kernel_size = [3, 3, 5, 5]
        config.backbone_config.stage_numb_of_layers = [3, 3, 3, 3]
        config.backbone_config.out_indices = [3, 4]
        config.backbone_config.use_learnable_affine_block = True
        config.num_feature_levels = 2
        config.encoder_ffn_dim = 512
        config.encode_proj_layers = [1]
        config.d_model = 128
        config.encoder_hidden_dim = 128
        config.decoder_ffn_dim = 512
        config.encoder_in_channels = [512, 1024]
        config.decoder_n_points = [6, 6]
        config.decoder_in_channels = [128, 128]
        config.feat_strides = [16, 32]
        config.depth_mult = 0.5
        config.decoder_layers = 3
        config.hidden_expansion = 0.34
        if model_name == "dfine_n_obj365":
            config.num_labels = 366
    else:
        config.backbone_config.hidden_sizes = [128, 256, 512, 1024]
        config.backbone_config.stem_channels = [3, 16, 16]
        config.backbone_config.stage_in_channels = [16, 64, 256, 512]
        config.backbone_config.stage_mid_channels = [16, 32, 64, 128]
        config.backbone_config.stage_out_channels = [64, 256, 512, 1024]
        config.backbone_config.stage_num_blocks = [1, 1, 2, 1]
        config.backbone_config.stage_downsample = [False, True, True, True]
        config.backbone_config.stage_light_block = [False, False, True, True]
        config.backbone_config.stage_kernel_size = [3, 3, 5, 5]
        config.backbone_config.stage_numb_of_layers = [3, 3, 3, 3]
        config.decoder_layers = 3
        config.hidden_expansion = 0.5
        config.depth_mult = 0.34
        config.decoder_n_points = [3, 6, 3]
        config.encoder_in_channels = [256, 512, 1024]
        config.backbone_config.use_learnable_affine_block = True
        if model_name == "dfine_s_obj365":
            config.num_labels = 366

    return config