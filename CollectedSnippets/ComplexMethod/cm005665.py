def install_all_output_capturing_hooks(model: PreTrainedModel, prefix: str | None = None) -> None:
    """
    Install the output recording hooks on all the modules in `model`. This will take care of correctly dispatching
    the `_can_record_outputs` property of each individual submodels in case of composite models.
    """
    # _can_record_outputs is None by default
    capture_flags = _CAN_RECORD_REGISTRY.get(str(model.__class__)) or {}  # there is a weak ref for executorch

    capture_tasks = []
    for key, layer_specs in capture_flags.items():
        if not isinstance(layer_specs, list):
            layer_specs = [layer_specs]
        for specs in layer_specs:
            if not isinstance(specs, OutputRecorder):
                index = 0 if "hidden_states" in key else 1
                class_name = None if not isinstance(specs, str) else specs
                target_class = specs if not isinstance(specs, str) else None
                specs = OutputRecorder(target_class=target_class, index=index, class_name=class_name)
            capture_tasks.append((key, specs))

    # Install the hooks
    prefix = prefix if prefix is not None else ""
    recursively_install_hooks(model, prefix, capture_tasks)
    # Mark the model as already hooked
    setattr(model, "_output_capturing_hooks_installed", True)