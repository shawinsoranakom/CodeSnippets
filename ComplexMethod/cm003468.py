def convert_yolos_checkpoint(
    yolos_name: str, checkpoint_path: str, pytorch_dump_folder_path: str, push_to_hub: bool = False
):
    """
    Copy/paste/tweak model's weights to our YOLOS structure.
    """
    config = get_yolos_config(yolos_name)

    # load original state_dict
    state_dict = torch.load(checkpoint_path, map_location="cpu", weights_only=True)["model"]

    # load 🤗 model
    model = YolosForObjectDetection(config)
    model.eval()
    new_state_dict = convert_state_dict(state_dict, model)
    model.load_state_dict(new_state_dict)

    # Check outputs on an image, prepared by YolosImageProcessor
    size = 800 if yolos_name != "yolos_ti" else 512
    image_processor = YolosImageProcessor(format="coco_detection", size=size)
    encoding = image_processor(images=prepare_img(), return_tensors="pt")
    outputs = model(**encoding)
    logits, pred_boxes = outputs.logits, outputs.pred_boxes

    expected_slice_logits, expected_slice_boxes = None, None
    if yolos_name == "yolos_ti":
        expected_slice_logits = torch.tensor(
            [[-39.5022, -11.9820, -17.6888], [-29.9574, -9.9769, -17.7691], [-42.3281, -20.7200, -30.6294]]
        )
        expected_slice_boxes = torch.tensor(
            [[0.4021, 0.0836, 0.7979], [0.0184, 0.2609, 0.0364], [0.1781, 0.2004, 0.2095]]
        )
    elif yolos_name == "yolos_s_200_pre":
        expected_slice_logits = torch.tensor(
            [[-24.0248, -10.3024, -14.8290], [-42.0392, -16.8200, -27.4334], [-27.2743, -11.8154, -18.7148]]
        )
        expected_slice_boxes = torch.tensor(
            [[0.2559, 0.5455, 0.4706], [0.2989, 0.7279, 0.1875], [0.7732, 0.4017, 0.4462]]
        )
    elif yolos_name == "yolos_s_300_pre":
        expected_slice_logits = torch.tensor(
            [[-36.2220, -14.4385, -23.5457], [-35.6970, -14.7583, -21.3935], [-31.5939, -13.6042, -16.8049]]
        )
        expected_slice_boxes = torch.tensor(
            [[0.7614, 0.2316, 0.4728], [0.7168, 0.4495, 0.3855], [0.4996, 0.1466, 0.9996]]
        )
    elif yolos_name == "yolos_s_dWr":
        expected_slice_logits = torch.tensor(
            [[-42.8668, -24.1049, -41.1690], [-34.7456, -14.1274, -24.9194], [-33.7898, -12.1946, -25.6495]]
        )
        expected_slice_boxes = torch.tensor(
            [[0.5587, 0.2773, 0.0605], [0.5004, 0.3014, 0.9994], [0.4999, 0.1548, 0.9994]]
        )
    elif yolos_name == "yolos_base":
        expected_slice_logits = torch.tensor(
            [[-40.6064, -24.3084, -32.6447], [-55.1990, -30.7719, -35.5877], [-51.4311, -33.3507, -35.6462]]
        )
        expected_slice_boxes = torch.tensor(
            [[0.5555, 0.2794, 0.0655], [0.9049, 0.2664, 0.1894], [0.9183, 0.1984, 0.1635]]
        )
    else:
        raise ValueError(f"Unknown yolos_name: {yolos_name}")

    assert torch.allclose(logits[0, :3, :3], expected_slice_logits, atol=1e-4)
    assert torch.allclose(pred_boxes[0, :3, :3], expected_slice_boxes, atol=1e-4)

    Path(pytorch_dump_folder_path).mkdir(exist_ok=True)
    print(f"Saving model {yolos_name} to {pytorch_dump_folder_path}")
    model.save_pretrained(pytorch_dump_folder_path)
    print(f"Saving image processor to {pytorch_dump_folder_path}")
    image_processor.save_pretrained(pytorch_dump_folder_path)

    if push_to_hub:
        model_mapping = {
            "yolos_ti": "yolos-tiny",
            "yolos_s_200_pre": "yolos-small",
            "yolos_s_300_pre": "yolos-small-300",
            "yolos_s_dWr": "yolos-small-dwr",
            "yolos_base": "yolos-base",
        }

        print("Pushing to the hub...")
        model_name = model_mapping[yolos_name]
        image_processor.push_to_hub(repo_id=f"hustvl/{model_name}")
        model.push_to_hub(repo_id=f"hustvl/{model_name}")