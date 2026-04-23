def _load_standard_training_states(
    ckpt_dir: str,
    model: Any,
    optimizer: torch.optim.Optimizer,
    map_location: torch.device,
) -> None:
    """Load model and optimizer for DDP / single-GPU."""
    model_dir = os.path.join(ckpt_dir, "model")
    model_to_load = model.module if hasattr(model, "module") else model

    is_adapter_ckpt = os.path.exists(os.path.join(model_dir, "adapter_config.json"))

    if is_adapter_ckpt:
        from peft import set_peft_model_state_dict

        adapter_file = os.path.join(model_dir, "adapter_model.safetensors")
        if not os.path.exists(adapter_file):
            adapter_file = os.path.join(model_dir, "adapter_model.bin")
            adapter_state = torch.load(adapter_file, map_location="cpu", weights_only=True)
        else:
            adapter_state = load_file(adapter_file, device="cpu")
        set_peft_model_state_dict(model_to_load, adapter_state)
    else:
        state_dict = {}
        for f in sorted(glob.glob(os.path.join(model_dir, "*.safetensors"))):
            state_dict.update(load_file(f, device="cpu"))
        if not state_dict:
            for f in sorted(glob.glob(os.path.join(model_dir, "*.bin"))):
                state_dict.update(torch.load(f, map_location="cpu", weights_only=True))
        if state_dict:
            model_to_load.load_state_dict(state_dict)
        else:
            logger.warning_rank0(f"No model weights found in {model_dir}, skipping model state restore.")

    optim_path = os.path.join(ckpt_dir, "optimizer", "state_dict.pt")
    if os.path.exists(optim_path):
        optimizer.load_state_dict(torch.load(optim_path, map_location=map_location, weights_only=True))