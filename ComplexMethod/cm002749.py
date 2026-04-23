def get_hiera_config(model_name: str, base_model: bool, mae_model: bool) -> HieraConfig:
    if model_name == "hiera-tiny-224":
        config = HieraConfig(depths=[1, 2, 7, 2])
    elif model_name == "hiera-small-224":
        config = HieraConfig(depths=[1, 2, 11, 2])
    elif model_name == "hiera-base-224":
        config = HieraConfig()
    elif model_name == "hiera-base-plus-224":
        config = HieraConfig(embed_dim=112, num_heads=[2, 4, 8, 16])
    elif model_name == "hiera-large-224":
        config = HieraConfig(embed_dim=144, num_heads=[2, 4, 8, 16], depths=[2, 6, 36, 4])
    elif model_name == "hiera-huge-224":
        config = HieraConfig(embed_dim=256, num_heads=[4, 8, 16, 32], depths=[2, 6, 36, 4])
    else:
        raise ValueError(f"Unrecognized model name: {model_name}")

    if base_model:
        pass
    elif mae_model:
        config.num_query_pool = 2
        config.decoder_hidden_size = 512
        config.decoder_depth = 8
        config.decoder_num_heads = 16
        # Table 3b from Hiera: A Hierarchical Vision Transformer without the Bells-and-Whistles
        config.mask_ratio = 0.6
    else:
        id2label, label2id, num_labels = get_labels_for_classifier(model_name)
        config.id2label = id2label
        config.label2id = label2id
        config.num_labels = num_labels

    return config