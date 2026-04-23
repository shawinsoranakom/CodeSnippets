def load_adapter(model: HFModel, adapter_name_or_path: Union[list[str], str], is_train: bool) -> HFModel:
    r"""Loads adapter(s) into the model.

    Determine adapter usage based on mode:
    - Training: Load the single adapter for continued training.
    - Inference: Merge all adapters to clean up the model.
    - Unmergeable: Keep the single adapter active without merging.
    """
    if not isinstance(adapter_name_or_path, list):
        adapter_name_or_path = [adapter_name_or_path]

    # TODO
    # Adapters fix for deepspeed and quant
    # Adapters fix for vision

    if is_train and len(adapter_name_or_path) > 1:
        raise ValueError(
            "When `adapter_name_or_path` is provided for training, only a single LoRA adapter is supported. "
            "Training will continue on the specified adapter. "
            "Please merge multiple adapters before starting a new LoRA adapter."
        )

    if is_train:
        adapter_to_merge = []
        adapter_to_resume = adapter_name_or_path[0]
    else:
        adapter_to_merge = adapter_name_or_path
        adapter_to_resume = None

    if adapter_to_merge:
        model = merge_adapters(model, adapter_to_merge)

    if adapter_to_resume is not None:
        model = PeftModel.from_pretrained(model, adapter_to_resume, is_trainable=is_train)
        if is_train:
            logger.info_rank0(
                f"Resuming training from existing LoRA adapter at {adapter_to_resume}. "
                "LoRA hyperparameters will be loaded from the adapter itself; "
                "the current LoRA configuration will be ignored. "
                "Merge the adapter into the base model before training if you want to start a new adapter."
            )

    return model