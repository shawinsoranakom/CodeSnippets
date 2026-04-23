def main():
    args = get_args()

    is_finetuned = "ft1k" in args.hf_checkpoint_name
    is_large = "large" in args.hf_checkpoint_name

    if is_finetuned:
        # To convert Beit's data2vec_vision to HF you need to copy
        # https://github.com/facebookresearch/data2vec_vision/blob/main/beit/modeling_finetune.py
        # into this folder.
        import modeling_finetune  # noqa: F401
    else:
        # To convert Beit's data2vec_vision to HF you need to copy
        # https://github.com/facebookresearch/data2vec_vision/blob/main/beit/modeling_cyclical.py
        # into this folder
        # IMPORTANT: Note that for now we've only converted the down-stream
        # model and not the full pretrained model. This means for the integration
        # test you need to add a `return x` after the following line:
        # https://github.com/facebookresearch/data2vec_vision/blob/af9a36349aaed59ae66e69b5dabeef2d62fdc5da/beit/modeling_cyclical.py#L197
        # to make the integration test pass.
        import modeling_cyclical  # noqa: F401

    # 1. Create model config
    config = Data2VecVisionConfig()
    if is_finetuned:
        config.use_relative_position_bias = True
        config.use_shared_relative_position_bias = False
        config.use_mean_pooling = True
        config.num_labels = 1000

        repo_id = "huggingface/label-files"
        filename = "imagenet-1k-id2label.json"
        id2label = json.load(open(hf_hub_download(repo_id, filename, repo_type="dataset"), "r"))
        id2label = {int(k): v for k, v in id2label.items()}
        config.id2label = id2label
        config.label2id = {v: k for k, v in id2label.items()}
    else:
        config.use_relative_position_bias = False
        config.use_shared_relative_position_bias = True
        config.use_mean_pooling = False

    if is_large:
        config.hidden_size = 1024
        config.intermediate_size = 4096
        config.num_hidden_layers = 24
        config.num_attention_heads = 16

    # 2. Load Beit model
    orig_model = load_beit_model(args, is_finetuned, is_large)
    orig_model.eval()

    # 3. Forward Beit model
    image_processor = BeitImageProcessor(size=config.image_size, do_center_crop=False)
    image = Image.open("../../../../tests/fixtures/tests_samples/COCO/000000039769.png")
    encoding = image_processor(images=image, return_tensors="pt")
    pixel_values = encoding["pixel_values"]

    orig_args = (pixel_values,) if is_finetuned else (pixel_values, None)
    with torch.no_grad():
        orig_model_output = orig_model(*orig_args)

    # 4. Load HF Data2VecVision model
    if is_finetuned:
        hf_model = Data2VecVisionForImageClassification(config)
        hf_model.eval()
        has_lm_head = False
        hf_prefix = "data2vec_vision."
    else:
        hf_model = Data2VecVisionModel(config)
        hf_model.eval()
        has_lm_head = True
        hf_prefix = ""

    rename_keys = create_rename_keys(config, hf_prefix=hf_prefix, has_lm_head=has_lm_head)
    state_dict = orig_model.state_dict()
    for src, dest in rename_keys:
        val = state_dict.pop(src)
        state_dict[dest] = val

    read_in_q_k_v(state_dict, config, hf_prefix=hf_prefix, has_lm_head=has_lm_head)
    missing_keys, unexpected_keys = hf_model.load_state_dict(state_dict, strict=False)
    print("HF missing", missing_keys)
    print("HF unexpected_keys", unexpected_keys)

    # 5. Forward HF Data2VecVision model
    with torch.no_grad():
        hf_model_output = hf_model(pixel_values)

    hf_output = hf_model_output.logits if is_finetuned else hf_model_output.last_hidden_state

    # 6. Compare
    max_absolute_diff = torch.max(torch.abs(hf_output - orig_model_output)).item()

    print(f"max_absolute_diff = {max_absolute_diff}")
    success = torch.allclose(hf_output, orig_model_output, atol=1e-3)
    print("Do both models output the same tensors?", "[PASS]" if success else "[FAIL]")
    if not success:
        raise Exception("Something went wRoNg")

    # 7. Save
    print(f"Saving to {args.hf_checkpoint_name}")
    hf_model.save_pretrained(args.hf_checkpoint_name)
    image_processor.save_pretrained(args.hf_checkpoint_name)