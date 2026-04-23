def convert_weights_and_push(save_directory: Path, model_name: str | None = None, push_to_hub: bool = True):
    filename = "imagenet-1k-id2label.json"
    num_labels = 1000

    repo_id = "huggingface/label-files"
    id2label = json.loads(Path(hf_hub_download(repo_id, filename, repo_type="dataset")).read_text())
    id2label = {int(k): v for k, v in id2label.items()}

    label2id = {v: k for k, v in id2label.items()}

    ImageNetPreTrainedConfig = partial(RegNetConfig, num_labels=num_labels, id2label=id2label, label2id=label2id)

    names_to_config = {
        "regnet-y-10b-seer": ImageNetPreTrainedConfig(
            depths=[2, 7, 17, 1], hidden_sizes=[2020, 4040, 11110, 28280], groups_width=1010
        ),
        # finetuned on imagenet
        "regnet-y-10b-seer-in1k": ImageNetPreTrainedConfig(
            depths=[2, 7, 17, 1], hidden_sizes=[2020, 4040, 11110, 28280], groups_width=1010
        ),
    }

    # add seer weights logic
    def load_using_classy_vision(checkpoint_url: str) -> tuple[dict, dict]:
        files = torch.hub.load_state_dict_from_url(checkpoint_url, model_dir=str(save_directory), map_location="cpu")
        # check if we have a head, if yes add it
        model_state_dict = files["classy_state_dict"]["base_model"]["model"]
        return model_state_dict["trunk"], model_state_dict["heads"]

    names_to_from_model = {
        "regnet-y-10b-seer": partial(
            load_using_classy_vision,
            "https://dl.fbaipublicfiles.com/vissl/model_zoo/seer_regnet10B/model_iteration124500_conso.torch",
        ),
        "regnet-y-10b-seer-in1k": partial(
            load_using_classy_vision,
            "https://dl.fbaipublicfiles.com/vissl/model_zoo/seer_finetuned/seer_10b_finetuned_in1k_model_phase28_conso.torch",
        ),
    }

    from_to_ours_keys = get_from_to_our_keys(model_name)

    if not (save_directory / f"{model_name}.pth").exists():
        logger.info("Loading original state_dict.")
        from_state_dict_trunk, from_state_dict_head = names_to_from_model[model_name]()
        from_state_dict = from_state_dict_trunk
        if "in1k" in model_name:
            # add the head
            from_state_dict = {**from_state_dict_trunk, **from_state_dict_head}
        logger.info("Done!")

        converted_state_dict = {}

        not_used_keys = list(from_state_dict.keys())
        regex = r"\.block.-part."
        # this is "interesting", so the original checkpoints have `block[0,1]-part` in each key name, we remove it
        for key in from_state_dict:
            # remove the weird "block[0,1]-part" from the key
            src_key = re.sub(regex, "", key)
            # now src_key from the model checkpoints is the one we got from the original model after tracing, so use it to get the correct destination key
            dest_key = from_to_ours_keys[src_key]
            # store the parameter with our key
            converted_state_dict[dest_key] = from_state_dict[key]
            not_used_keys.remove(key)
        # check that all keys have been updated
        assert len(not_used_keys) == 0, f"Some keys where not used {','.join(not_used_keys)}"

        logger.info(f"The following keys were not used: {','.join(not_used_keys)}")

        # save our state dict to disk
        torch.save(converted_state_dict, save_directory / f"{model_name}.pth")

        del converted_state_dict
    else:
        logger.info("The state_dict was already stored on disk.")
    if push_to_hub:
        logger.info(f"Token is {os.environ['HF_TOKEN']}")
        logger.info("Loading our model.")
        # create our model
        our_config = names_to_config[model_name]
        our_model_func = RegNetModel
        if "in1k" in model_name:
            our_model_func = RegNetForImageClassification
        with torch.device("meta"):
            our_model = our_model_func(our_config)
        logger.info("Loading state_dict in our model.")
        # load state dict
        state_dict_keys = our_model.state_dict().keys()
        state_dict = load_state_dict(save_directory / f"{model_name}.pth", weights_only=True)
        fixed_state_dict = state_dict = {our_model._fix_state_dict_key_on_load(k)[0]: v for k, v in state_dict.items()}
        _load_state_dict_into_meta_model(
            our_model,
            fixed_state_dict,
            start_prefix="",
            expected_keys=state_dict_keys,
        )
        logger.info("Finally, pushing!")
        # push it to hub
        our_model.push_to_hub(repo_id=model_name, commit_message="Add model", output_dir=save_directory / model_name)
        size = 384
        # we can use the convnext one
        image_processor = AutoImageProcessor.from_pretrained("facebook/convnext-base-224-22k-1k", size=size)
        image_processor.push_to_hub(
            repo_id=model_name, commit_message="Add image processor", output_dir=save_directory / model_name
        )