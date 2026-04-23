def main(args: argparse.Namespace):
    model_params = CLASSIFIERS[args.model_name]
    id2label = get_id2label_mapping(model_params["dataset"])

    if not len(id2label) == model_params["num_labels"]:
        raise ValueError(
            f"Number of labels in id2label mapping ({len(id2label)}) does not "
            f"match number of labels in model ({model_params['num_labels']})"
        )

    model = VJEPA2ForVideoClassification.from_pretrained(
        model_params["base_model"],
        num_labels=model_params["num_labels"],
        id2label=id2label,
        frames_per_clip=model_params["frames_per_clip"],
    )
    processor = VJEPA2VideoProcessor.from_pretrained(model_params["base_model"])

    # load and convert classifier checkpoint
    checkpoint = torch.hub.load_state_dict_from_url(model_params["checkpoint"])
    state_dict = checkpoint["classifiers"][0]

    state_dict_qkv_split = split_qkv(state_dict)
    key_mapping = convert_old_keys_to_new_keys(state_dict_qkv_split.keys())
    converted_state_dict2 = {key_mapping[k]: v for k, v in state_dict_qkv_split.items()}

    result = model.load_state_dict(converted_state_dict2, strict=False)
    if result.unexpected_keys:
        raise ValueError(f"Error loading state dict: {result.unexpected_keys}")

    if not args.skip_verification:
        # get inputs
        video_reader = get_video()
        frame_indexes = np.arange(0, 128, 128 / model_params["frames_per_clip"])
        video = video_reader.get_batch(frame_indexes).asnumpy()
        inputs = processor(video, return_tensors="pt").to(device)

        # run model
        model.to(device).eval()
        with torch.no_grad():
            outputs = model(**inputs)

        # compare results
        probs = torch.softmax(outputs.logits, dim=-1)
        top_prob, top_idx = probs.topk(1)
        top_prob, top_idx = top_prob.item(), top_idx.item()
        label = id2label[top_idx]
        expected_id, expected_prob, expected_label = model_params["result"]

        if not top_idx == expected_id:
            raise ValueError(f"Expected id {expected_id} but got {top_idx}")
        if not label == expected_label:
            raise ValueError(f"Expected label {expected_label} but got {label}")
        if not np.isclose(top_prob, expected_prob, atol=1e-3):
            raise ValueError(f"Expected prob {expected_prob} but got {top_prob}")
        print("Verification passed")

    output_dir = os.path.join(args.base_dir, args.model_name)
    model.save_pretrained(output_dir)
    processor.save_pretrained(output_dir)

    if args.push_to_hub:
        api = HfApi()
        repo_id = f"{args.repo_org}/{args.model_name}"
        if not api.repo_exists(repo_id):
            api.create_repo(repo_id, repo_type="model")
        api.upload_folder(folder_path=output_dir, repo_id=repo_id, repo_type="model")