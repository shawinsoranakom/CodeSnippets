def convert_weight_and_push(
    hidden_sizes: int, name: str, config: LevitConfig, save_directory: Path, push_to_hub: bool = True
):
    print(f"Converting {name}...")

    with torch.no_grad():
        if hidden_sizes == 128:
            if name[-1] == "S":
                from_model = timm.create_model("levit_128s", pretrained=True)
            else:
                from_model = timm.create_model("levit_128", pretrained=True)
        if hidden_sizes == 192:
            from_model = timm.create_model("levit_192", pretrained=True)
        if hidden_sizes == 256:
            from_model = timm.create_model("levit_256", pretrained=True)
        if hidden_sizes == 384:
            from_model = timm.create_model("levit_384", pretrained=True)

        from_model.eval()
        our_model = LevitForImageClassificationWithTeacher(config).eval()
        huggingface_weights = OrderedDict()

        weights = from_model.state_dict()
        og_keys = list(from_model.state_dict().keys())
        new_keys = list(our_model.state_dict().keys())
        print(len(og_keys), len(new_keys))
        for i in range(len(og_keys)):
            huggingface_weights[new_keys[i]] = weights[og_keys[i]]
        our_model.load_state_dict(huggingface_weights)

        x = torch.randn((2, 3, 224, 224))
        out1 = from_model(x)
        out2 = our_model(x).logits

    assert torch.allclose(out1, out2), "The model logits don't match the original one."

    checkpoint_name = name
    print(checkpoint_name)

    if push_to_hub:
        our_model.save_pretrained(save_directory / checkpoint_name)
        image_processor = LevitImageProcessor()
        image_processor.save_pretrained(save_directory / checkpoint_name)

        print(f"Pushed {checkpoint_name}")