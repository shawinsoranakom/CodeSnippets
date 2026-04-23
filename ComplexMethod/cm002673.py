def patch_output_recorders(model: nn.Module) -> None:
    """
    Patch the model instance's output recorders to use the registered replacement classes.

    This function updates output recorders in a model's submodules to use monkey-patched replacement
    classes. Output recorders are used by the transformers library to track intermediate outputs during
    forward passes (via the `_can_record_outputs` attribute). When classes are monkey-patched, these
    recorders need to be updated to reference the new classes.

    This is automatically called during model initialization when loading with `from_pretrained` or
    `from_config`. You typically don't need to call this manually unless you're constructing models
    in custom ways.

    Note:
        The `_can_record_outputs` attribute is a class-level attribute that maps output names to either:
        - `OutputRecorder` instances that have a `target_class` attribute
        - Class types directly

        This function patches both cases to use the replacement classes from the monkey patch registry.

    Args:
        model (`nn.Module`):
            The model instance whose output recorders should be patched. All submodules will be
            traversed to find and patch their `_can_record_outputs` attributes.

    Example:
        ```python
        from transformers import AutoModelForCausalLM
        from transformers.monkey_patching import register_patch_mapping, patch_output_recorders

        # Register a patch
        register_patch_mapping(mapping={"Qwen2MoeExperts": CustomExperts})

        # If you construct a model manually (without from_pretrained), patch recorders
        model = Qwen2MoeModel(config)
        patch_output_recorders(model)  # Updates output recorders to use CustomExperts
        ```
    """

    mapping = get_patch_mapping()
    if not mapping:
        return

    for submodule in model.modules():
        if hasattr(submodule, "_can_record_outputs") and submodule._can_record_outputs is not None:
            for output, recorder in submodule._can_record_outputs.items():
                if isinstance(recorder, OutputRecorder):
                    # Check if target class matches any registered pattern or exact name
                    replacement_class = _find_replacement_class(recorder.target_class.__name__, mapping)
                    if replacement_class is not None:
                        recorder.target_class = replacement_class
                elif isinstance(recorder, type):
                    # Check if class type matches any registered pattern or exact name
                    replacement_class = _find_replacement_class(recorder.__name__, mapping)
                    if replacement_class is not None:
                        submodule._can_record_outputs[output] = replacement_class