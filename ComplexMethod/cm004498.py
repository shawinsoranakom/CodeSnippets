def convert_weight_and_push(
    name: str,
    from_model_func: Callable[[], nn.Module],
    our_model_func: Callable[[], nn.Module],
    config: RegNetConfig,
    save_directory: Path,
    push_to_hub: bool = True,
):
    print(f"Converting {name}...")
    with torch.no_grad():
        from_model, from_state_dict = from_model_func()
        our_model = our_model_func(config).eval()
        module_transfer = ModuleTransfer(src=from_model, dest=our_model, raise_if_mismatch=False)
        x = torch.randn((1, 3, 224, 224))
        module_transfer(x)

    if from_state_dict is not None:
        keys = []
        # for seer - in1k finetuned we have to manually copy the head
        if "seer" in name and "in1k" in name:
            keys = [("0.clf.0.weight", "classifier.1.weight"), ("0.clf.0.bias", "classifier.1.bias")]
        to_state_dict = manually_copy_vissl_head(from_state_dict, our_model.state_dict(), keys)
        our_model.load_state_dict(to_state_dict)

    our_outputs = our_model(x, output_hidden_states=True)
    our_output = (
        our_outputs.logits if isinstance(our_model, RegNetForImageClassification) else our_outputs.last_hidden_state
    )

    from_output = from_model(x)
    from_output = from_output[-1] if isinstance(from_output, list) else from_output

    # now since I don't want to use any config files, vissl seer model doesn't actually have an head, so let's just check the last hidden state
    if "seer" in name and "in1k" in name:
        our_output = our_outputs.hidden_states[-1]

    assert torch.allclose(from_output, our_output), "The model logits don't match the original one."

    if push_to_hub:
        our_model.push_to_hub(repo_id=name)

        size = 224 if "seer" not in name else 384
        # we can use the convnext one
        image_processor = AutoImageProcessor.from_pretrained("facebook/convnext-base-224-22k-1k", size=size)
        image_processor.push_to_hub(repo_id=name)

        print(f"Pushed {name}")