def write_model(model_name, model_path, push_to_hub, check_logits=True):
    # ------------------------------------------------------------
    # Vision model params and config
    # ------------------------------------------------------------

    # params from config
    config = get_config(model_name)

    # ------------------------------------------------------------
    # Convert weights
    # ------------------------------------------------------------

    # load original state_dict
    filename = MODEL_TO_FILE_NAME_MAPPING[model_name]
    print(f"Fetching all parameters from the checkpoint at {filename}...")

    checkpoint_path = hf_hub_download(
        repo_id="nielsr/vitpose-original-checkpoints", filename=filename, repo_type="model"
    )

    print("Converting model...")
    original_state_dict = torch.load(checkpoint_path, map_location="cpu", weights_only=True)["state_dict"]
    all_keys = list(original_state_dict.keys())
    new_keys = convert_old_keys_to_new_keys(all_keys)

    dim = config.backbone_config.hidden_size

    state_dict = {}
    for key in all_keys:
        new_key = new_keys[key]
        value = original_state_dict[key]

        if re.search("associate_heads", new_key) or re.search("backbone.cls_token", new_key):
            # This associated_heads is concept of auxiliary head so does not require in inference stage.
            # backbone.cls_token is optional forward function for dynamically change of size, see detail in https://github.com/ViTAE-Transformer/ViTPose/issues/34
            pass
        elif re.search("qkv", new_key):
            state_dict[new_key.replace("self.qkv", "attention.query")] = value[:dim]
            state_dict[new_key.replace("self.qkv", "attention.key")] = value[dim : dim * 2]
            state_dict[new_key.replace("self.qkv", "attention.value")] = value[-dim:]
        elif re.search("head", new_key) and not config.use_simple_decoder:
            # Pattern for deconvolution layers
            deconv_pattern = r"deconv_layers\.(0|3)\.weight"
            new_key = re.sub(deconv_pattern, lambda m: f"deconv{int(m.group(1)) // 3 + 1}.weight", new_key)
            # Pattern for batch normalization layers
            bn_patterns = [
                (r"deconv_layers\.(\d+)\.weight", r"batchnorm\1.weight"),
                (r"deconv_layers\.(\d+)\.bias", r"batchnorm\1.bias"),
                (r"deconv_layers\.(\d+)\.running_mean", r"batchnorm\1.running_mean"),
                (r"deconv_layers\.(\d+)\.running_var", r"batchnorm\1.running_var"),
                (r"deconv_layers\.(\d+)\.num_batches_tracked", r"batchnorm\1.num_batches_tracked"),
            ]

            for pattern, replacement in bn_patterns:
                if re.search(pattern, new_key):
                    # Convert the layer number to the correct batch norm index
                    layer_num = int(re.search(pattern, key).group(1))
                    bn_num = layer_num // 3 + 1
                    new_key = re.sub(pattern, replacement.replace(r"\1", str(bn_num)), new_key)
            state_dict[new_key] = value
        else:
            state_dict[new_key] = value

    print("Loading the checkpoint in a Vitpose model.")
    model = VitPoseForPoseEstimation(config)
    model.eval()
    model.load_state_dict(state_dict)
    print("Checkpoint loaded successfully.")

    # create image processor
    image_processor = VitPoseImageProcessor()

    # verify image processor
    image = prepare_img()
    boxes = [[[412.8, 157.61, 53.05, 138.01], [384.43, 172.21, 15.12, 35.74]]]
    pixel_values = image_processor(images=image, boxes=boxes, return_tensors="pt").pixel_values

    filepath = hf_hub_download(repo_id="nielsr/test-image", filename="vitpose_batch_data.pt", repo_type="dataset")
    original_pixel_values = torch.load(filepath, map_location="cpu", weights_only=True)["img"]
    # we allow for a small difference in the pixel values due to the original repository using cv2
    assert torch.allclose(pixel_values, original_pixel_values, atol=1e-1)

    dataset_index = torch.tensor([0])

    with torch.no_grad():
        print("Shape of original_pixel_values: ", original_pixel_values.shape)
        print("First values of original_pixel_values: ", original_pixel_values[0, 0, :3, :3])

        # first forward pass
        outputs = model(original_pixel_values, dataset_index=dataset_index)
        output_heatmap = outputs.heatmaps

        print("Shape of output_heatmap: ", output_heatmap.shape)
        print("First values: ", output_heatmap[0, 0, :3, :3])

        # second forward pass (flipped)
        # this is done since the model uses `flip_test=True` in its test config
        original_pixel_values_flipped = torch.flip(original_pixel_values, [3])
        outputs_flipped = model(
            original_pixel_values_flipped,
            dataset_index=dataset_index,
            flip_pairs=torch.tensor([[1, 2], [3, 4], [5, 6], [7, 8], [9, 10], [11, 12], [13, 14], [15, 16]]),
        )
        output_flipped_heatmap = outputs_flipped.heatmaps

    outputs.heatmaps = (output_heatmap + output_flipped_heatmap) * 0.5

    # Verify pose_results
    pose_results = image_processor.post_process_pose_estimation(outputs, boxes=boxes)[0]

    if check_logits:
        # Simple decoder checkpoints
        if model_name == "vitpose-base-simple":
            assert torch.allclose(
                pose_results[1]["keypoints"][0],
                torch.tensor([3.98180511e02, 1.81808380e02]),
                atol=5e-2,
            )
            assert torch.allclose(
                pose_results[1]["scores"][0],
                torch.tensor([8.66642594e-01]),
                atol=5e-2,
            )
        # Classic decoder checkpoints
        elif model_name == "vitpose-base":
            assert torch.allclose(
                pose_results[1]["keypoints"][0],
                torch.tensor([3.9807913e02, 1.8182812e02]),
                atol=5e-2,
            )
            assert torch.allclose(
                pose_results[1]["scores"][0],
                torch.tensor([8.8235235e-01]),
                atol=5e-2,
            )
        # COCO-AIC-MPII checkpoints
        elif model_name == "vitpose-base-coco-aic-mpii":
            assert torch.allclose(
                pose_results[1]["keypoints"][0],
                torch.tensor([3.98305542e02, 1.81741592e02]),
                atol=5e-2,
            )
            assert torch.allclose(
                pose_results[1]["scores"][0],
                torch.tensor([8.69966745e-01]),
                atol=5e-2,
            )
        # VitPose+ models
        elif model_name == "vitpose-plus-small":
            assert torch.allclose(
                pose_results[1]["keypoints"][0],
                torch.tensor([398.1597, 181.6902]),
                atol=5e-2,
            )
            assert torch.allclose(
                pose_results[1]["scores"][0],
                torch.tensor(0.9051),
                atol=5e-2,
            )
        elif model_name == "vitpose-plus-base":
            assert torch.allclose(
                pose_results[1]["keypoints"][0],
                torch.tensor([3.98201294e02, 1.81728302e02]),
                atol=5e-2,
            )
            assert torch.allclose(
                pose_results[1]["scores"][0],
                torch.tensor([8.75046968e-01]),
                atol=5e-2,
            )
        elif model_name == "vitpose-plus-large":
            assert torch.allclose(
                pose_results[1]["keypoints"][0],
                torch.tensor([398.1409, 181.7412]),
                atol=5e-2,
            )
            assert torch.allclose(
                pose_results[1]["scores"][0],
                torch.tensor(0.8746),
                atol=5e-2,
            )
        elif model_name == "vitpose-plus-huge":
            assert torch.allclose(
                pose_results[1]["keypoints"][0],
                torch.tensor([398.2079, 181.8026]),
                atol=5e-2,
            )
            assert torch.allclose(
                pose_results[1]["scores"][0],
                torch.tensor(0.8693),
                atol=5e-2,
            )
        else:
            raise ValueError("Model not supported")
    print("Conversion successfully done.")

    if model_path is not None:
        os.makedirs(model_path, exist_ok=True)
        model.save_pretrained(model_path)
        image_processor.save_pretrained(model_path)

    if push_to_hub:
        print(f"Pushing model and image processor for {model_name} to hub")
        # we created a community organization on the hub for this model
        # maintained by the Transformers team
        model.push_to_hub(f"usyd-community/{model_name}")
        image_processor.push_to_hub(f"usyd-community/{model_name}")