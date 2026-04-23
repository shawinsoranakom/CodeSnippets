def convert_vit_checkpoint(vit_name, pytorch_dump_folder_path):
    """
    Copy/paste/tweak model's weights to our ViT structure.
    """

    # define default ViT configuration
    config = ViTConfig()
    base_model = False

    # load original model from timm
    timm_model = timm.create_model(vit_name, pretrained=True)
    timm_model.eval()

    # detect unsupported ViT models in transformers
    # fc_norm is present
    if not isinstance(getattr(timm_model, "fc_norm", None), torch.nn.Identity):
        raise ValueError(f"{vit_name} is not supported in transformers because of the presence of fc_norm.")

    # use of global average pooling in combination (or without) class token
    if getattr(timm_model, "global_pool", None) == "avg":
        raise ValueError(f"{vit_name} is not supported in transformers because of use of global average pooling.")

    # CLIP style vit with norm_pre layer present
    if "clip" in vit_name and not isinstance(getattr(timm_model, "norm_pre", None), torch.nn.Identity):
        raise ValueError(
            f"{vit_name} is not supported in transformers because it's a CLIP style ViT with norm_pre layer."
        )

    # SigLIP style vit with attn_pool layer present
    if "siglip" in vit_name and getattr(timm_model, "global_pool", None) == "map":
        raise ValueError(
            f"{vit_name} is not supported in transformers because it's a SigLIP style ViT with attn_pool."
        )

    # use of layer scale in ViT model blocks
    if not isinstance(getattr(timm_model.blocks[0], "ls1", None), torch.nn.Identity) or not isinstance(
        getattr(timm_model.blocks[0], "ls2", None), torch.nn.Identity
    ):
        raise ValueError(f"{vit_name} is not supported in transformers because it uses a layer scale in its blocks.")

    # Hybrid ResNet-ViTs
    if not isinstance(timm_model.patch_embed, timm.layers.PatchEmbed):
        raise ValueError(f"{vit_name} is not supported in transformers because it is a hybrid ResNet-ViT.")

    # get patch size and image size from the patch embedding submodule
    config.patch_size = timm_model.patch_embed.patch_size[0]
    config.image_size = timm_model.patch_embed.img_size[0]

    # retrieve architecture-specific parameters from the timm model
    config.hidden_size = timm_model.embed_dim
    config.intermediate_size = timm_model.blocks[0].mlp.fc1.out_features
    config.num_hidden_layers = len(timm_model.blocks)
    config.num_attention_heads = timm_model.blocks[0].attn.num_heads

    # check whether the model has a classification head or not
    if timm_model.num_classes != 0:
        config.num_labels = timm_model.num_classes
        # infer ImageNet subset from timm model
        imagenet_subset = infer_imagenet_subset(timm_model)
        dataset_info = ImageNetInfo(imagenet_subset)
        config.id2label = {i: dataset_info.index_to_label_name(i) for i in range(dataset_info.num_classes())}
        config.label2id = {v: k for k, v in config.id2label.items()}
    else:
        print(f"{vit_name} is going to be converted as a feature extractor only.")
        base_model = True

    # load state_dict of original model
    state_dict = timm_model.state_dict()

    # remove and rename some keys in the state dict
    if base_model:
        remove_classification_head_(state_dict)
    rename_keys = create_rename_keys(config, base_model)
    for src, dest in rename_keys:
        rename_key(state_dict, src, dest)
    read_in_q_k_v(state_dict, config, base_model)

    # load HuggingFace model
    if base_model:
        model = ViTModel(config, add_pooling_layer=False).eval()
    else:
        model = ViTForImageClassification(config).eval()
    model.load_state_dict(state_dict)

    # Check outputs on an image, prepared by ViTImageProcessor/DeiTImageProcessor
    if "deit" in vit_name:
        image_processor = DeiTImageProcessor(size=config.image_size)
    else:
        image_processor = ViTImageProcessor(size=config.image_size)
    encoding = image_processor(images=prepare_img(), return_tensors="pt")
    pixel_values = encoding["pixel_values"]
    outputs = model(pixel_values)

    if base_model:
        timm_pooled_output = timm_model.forward_features(pixel_values)
        assert timm_pooled_output.shape == outputs.last_hidden_state.shape
        assert torch.allclose(timm_pooled_output, outputs.last_hidden_state, atol=1e-1)
    else:
        timm_logits = timm_model(pixel_values)
        assert timm_logits.shape == outputs.logits.shape
        assert torch.allclose(timm_logits, outputs.logits, atol=1e-3)

    Path(pytorch_dump_folder_path).mkdir(exist_ok=True)
    print(f"Saving model {vit_name} to {pytorch_dump_folder_path}")
    model.save_pretrained(pytorch_dump_folder_path)
    print(f"Saving image processor to {pytorch_dump_folder_path}")
    image_processor.save_pretrained(pytorch_dump_folder_path)