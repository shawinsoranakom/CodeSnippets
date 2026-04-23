def _process_example_section(
    func_documentation, func, parent_class, class_name, model_name_lowercase, config_class, checkpoint, indent_level
):
    """
    Process the example section of the docstring.

    Args:
        func_documentation (`str`): Existing function documentation (manually specified in the docstring)
        func (`function`): Function being processed
        parent_class (`class`): Parent class of the function
        class_name (`str`): Name of the class
        model_name_lowercase (`str`): Lowercase model name
        config_class (`str`): Config class for the model
        checkpoint: Checkpoint to use in examples
        indent_level (`int`): Indentation level
    """
    # Import here to avoid circular import
    from transformers.models import auto as auto_module

    example_docstring = ""

    # Use existing example section if available (with or without an "Example:" header)
    if func_documentation is not None and (match := _re_example.search(func_documentation)):
        example_docstring = func_documentation[match.start() :]
        example_docstring = "\n" + set_min_indent(example_docstring, indent_level + 4)
    # Skip examples for processors
    elif _is_processor_class(func, parent_class):
        # Processors don't get auto-generated examples
        return example_docstring
    # No examples for __init__ methods or if the class is not a model
    elif parent_class is None and model_name_lowercase is not None:
        global _re_model_task
        if _re_model_task is None:
            _re_model_task = re.compile(rf"({'|'.join(PT_SAMPLE_DOCSTRINGS.keys())})")
        model_task = _re_model_task.search(class_name)
        CONFIG_MAPPING = auto_module.configuration_auto.CONFIG_MAPPING

        # Get checkpoint example
        if (checkpoint_example := checkpoint) is None:
            try:
                checkpoint_example = get_checkpoint_from_config_class(CONFIG_MAPPING[model_name_lowercase])
            except KeyError:
                # For models with inconsistent lowercase model name
                if model_name_lowercase in HARDCODED_CONFIG_FOR_MODELS:
                    CONFIG_MAPPING_NAMES = auto_module.configuration_auto.CONFIG_MAPPING_NAMES
                    config_class_name = HARDCODED_CONFIG_FOR_MODELS[model_name_lowercase]
                    if config_class_name in CONFIG_MAPPING_NAMES.values():
                        model_name_for_auto_config = [
                            k for k, v in CONFIG_MAPPING_NAMES.items() if v == config_class_name
                        ][0]
                        if model_name_for_auto_config in CONFIG_MAPPING:
                            checkpoint_example = get_checkpoint_from_config_class(
                                CONFIG_MAPPING[model_name_for_auto_config]
                            )

        # Add example based on model task
        if model_task is not None:
            if checkpoint_example is not None:
                example_annotation = ""
                task = model_task.group()
                example_annotation = PT_SAMPLE_DOCSTRINGS[task].format(
                    model_class=class_name,
                    checkpoint=checkpoint_example,
                    expected_output="...",
                    expected_loss="...",
                    qa_target_start_index=14,
                    qa_target_end_index=15,
                    mask="<mask>",
                )
                example_docstring = set_min_indent(example_annotation, indent_level + 4)
            else:
                print(
                    f"[ERROR] No checkpoint found for {class_name}.{func.__name__}. Please add a `checkpoint` arg to `auto_docstring` or add one in {config_class}'s docstring"
                )
        else:
            # Check if the model is in a pipeline to get an example
            for name_model_list_for_task in MODELS_TO_PIPELINE:
                try:
                    model_list_for_task = getattr(auto_module.modeling_auto, name_model_list_for_task)
                except (ImportError, AttributeError):
                    continue
                if class_name in model_list_for_task.values():
                    pipeline_name = MODELS_TO_PIPELINE[name_model_list_for_task]
                    example_annotation = PIPELINE_TASKS_TO_SAMPLE_DOCSTRINGS[pipeline_name].format(
                        model_class=class_name,
                        checkpoint=checkpoint_example,
                        expected_output="...",
                        expected_loss="...",
                        qa_target_start_index=14,
                        qa_target_end_index=15,
                    )
                    example_docstring = set_min_indent(example_annotation, indent_level + 4)
                    break

    return example_docstring