def convert_vit_checkpoint(model_name, pytorch_dump_folder_path, base_model=True):
    """
    Copy/paste/tweak model's weights to our ViT structure.
    """

    # define default ViT configuration
    config = ViTConfig()
    # patch_size
    if model_name[-1] == "8":
        config.patch_size = 8
    # set labels if required
    if not base_model:
        config.num_labels = 1000
        repo_id = "huggingface/label-files"
        filename = "imagenet-1k-id2label.json"
        id2label = json.load(open(hf_hub_download(repo_id, filename, repo_type="dataset"), "r"))
        id2label = {int(k): v for k, v in id2label.items()}
        config.id2label = id2label
        config.label2id = {v: k for k, v in id2label.items()}
    # size of the architecture
    if model_name in ["dino_vits8", "dino_vits16"]:
        config.hidden_size = 384
        config.intermediate_size = 1536
        config.num_hidden_layers = 12
        config.num_attention_heads = 6

    # load original model from torch hub
    original_model = torch.hub.load("facebookresearch/dino:main", model_name)
    original_model.eval()

    # load state_dict of original model, remove and rename some keys
    state_dict = original_model.state_dict()
    if base_model:
        remove_classification_head_(state_dict)
    rename_keys = create_rename_keys(config, base_model=base_model)
    for src, dest in rename_keys:
        rename_key(state_dict, src, dest)
    read_in_q_k_v(state_dict, config, base_model)

    # load HuggingFace model
    if base_model:
        model = ViTModel(config, add_pooling_layer=False).eval()
    else:
        model = ViTForImageClassification(config).eval()
    model.load_state_dict(state_dict)

    # Check outputs on an image, prepared by ViTImageProcessor
    image_processor = ViTImageProcessor()
    encoding = image_processor(images=prepare_img(), return_tensors="pt")
    pixel_values = encoding["pixel_values"]
    outputs = model(pixel_values)

    if base_model:
        final_hidden_state_cls_token = original_model(pixel_values)
        assert torch.allclose(final_hidden_state_cls_token, outputs.last_hidden_state[:, 0, :], atol=1e-1)
    else:
        logits = original_model(pixel_values)
        assert logits.shape == outputs.logits.shape
        assert torch.allclose(logits, outputs.logits, atol=1e-3)

    Path(pytorch_dump_folder_path).mkdir(exist_ok=True)
    print(f"Saving model {model_name} to {pytorch_dump_folder_path}")
    model.save_pretrained(pytorch_dump_folder_path)
    print(f"Saving image processor to {pytorch_dump_folder_path}")
    image_processor.save_pretrained(pytorch_dump_folder_path)