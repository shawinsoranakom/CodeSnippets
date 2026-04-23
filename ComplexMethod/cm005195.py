def convert_checkpoint(
    checkpoint_filename: str,
    image_size: int,
    num_frames: int,
    output_dir: str | None = None,
    verify: bool = False,
    reference_repo_path: str | None = None,
    push_to_hub: bool = False,
) -> None:
    checkpoint_path = hf_hub_download(repo_id=MODEL_REPO_ID, filename=checkpoint_filename)
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    original_state_dict = checkpoint.get("model", checkpoint)

    config = infer_videomt_config(
        original_state_dict, checkpoint_filename, image_size=image_size, num_frames=num_frames
    )

    ckpt_cfg = CHECKPOINT_CONFIGS.get(checkpoint_filename)
    if ckpt_cfg is not None:
        id2label = DATASET_TO_ID2LABEL[ckpt_cfg["dataset"]]
        if len(id2label) != config.num_labels:
            raise ValueError(
                f"id2label length ({len(id2label)}) does not match num_labels ({config.num_labels}) "
                f"for checkpoint '{checkpoint_filename}'."
            )
        config.id2label = id2label
        config.label2id = {v: k for k, v in id2label.items()}

    model = VideomtForUniversalSegmentation(config)
    converted_state_dict, consumed_keys = convert_state_dict(original_state_dict)

    load_info = model.load_state_dict(converted_state_dict, strict=False)

    dummy_video = torch.randn(1, num_frames, 3, config.image_size, config.image_size)
    with torch.no_grad():
        outputs = model(pixel_values_videos=dummy_video)

    if (
        not torch.isfinite(outputs.class_queries_logits).all()
        or not torch.isfinite(outputs.masks_queries_logits).all()
    ):
        raise ValueError("Converted model produced non-finite outputs.")

    print(f"checkpoint={checkpoint_filename}")
    print(f"missing_keys={len(load_info.missing_keys)}")
    print(f"unexpected_keys={len(load_info.unexpected_keys)}")
    print(f"class_logits_shape={tuple(outputs.class_queries_logits.shape)}")
    print(f"mask_logits_shape={tuple(outputs.masks_queries_logits.shape)}")

    if load_info.missing_keys:
        print("missing_key_list=")
        for key in load_info.missing_keys:
            print(f"  - {key}")

    if load_info.unexpected_keys:
        print("unexpected_key_list=")
        for key in load_info.unexpected_keys:
            print(f"  - {key}")

    unconverted_source_keys = sorted(set(original_state_dict.keys()) - consumed_keys)
    print(f"unconverted_source_keys={len(unconverted_source_keys)}")
    if unconverted_source_keys:
        print("unconverted_source_key_list=")
        for key in unconverted_source_keys:
            print(f"  - {key}")

        query_updater_keys = [key for key in unconverted_source_keys if "query_updater" in key]
        if query_updater_keys:
            print("note=unconverted_query_updater_keys_detected; temporal-frame forward parity may differ")

    if output_dir is not None:
        model.save_pretrained(output_dir)
        config.save_pretrained(output_dir)
        print(f"saved_to={output_dir}")

    if push_to_hub:
        ckpt_cfg = CHECKPOINT_CONFIGS.get(checkpoint_filename)
        if ckpt_cfg is None:
            raise ValueError(
                f"Cannot push to Hub: checkpoint '{checkpoint_filename}' has no entry in CHECKPOINT_CONFIGS."
            )
        hub_name = ckpt_cfg["hub_name"]
        model.push_to_hub(hub_name)
        print(f"pushed_to_hub={hub_name}")

    if verify:
        verify_ok = verify_conversion_against_github_reference(
            hf_model=model,
            original_state_dict=original_state_dict,
            checkpoint_filename=checkpoint_filename,
            image_size=image_size,
            num_frames=num_frames,
            reference_repo_path=reference_repo_path,
        )
        print(f"verify_ok={verify_ok}")