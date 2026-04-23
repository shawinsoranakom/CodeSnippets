def get_user_input():
    """
    Ask the user for the necessary inputs to add the new model.
    """
    from transformers.models.auto.configuration_auto import CONFIG_MAPPING_NAMES

    model_types = list(CONFIG_MAPPING_NAMES.keys())

    # Get old model type
    valid_model_type = False
    while not valid_model_type:
        old_model_type = input(
            "What model would you like to duplicate? Please provide it as lowercase, e.g. `llama`): "
        )
        if old_model_type in model_types:
            valid_model_type = True
        else:
            print(f"{old_model_type} is not a valid model type.")
            near_choices = difflib.get_close_matches(old_model_type, model_types)
            if len(near_choices) >= 1:
                if len(near_choices) > 1:
                    near_choices = " or ".join(near_choices)
                print(f"Did you mean {near_choices}?")

    old_model_infos = ModelInfos(old_model_type)

    # Ask for the new model name
    new_lowercase_name = get_user_field(
        "What is the new model name? Please provide it as snake lowercase, e.g. `new_model`?"
    )
    new_model_paper_name = get_user_field(
        "What is the fully cased name you would like to appear in the doc (e.g. `NeW ModEl`)? ",
        default_value="".join(x.title() for x in new_lowercase_name.split("_")),
    )

    # Ask if we want to add individual processor classes as well
    add_tokenizer = False
    add_fast_tokenizer = False
    add_image_processor = False
    add_video_processor = False
    add_feature_extractor = False
    add_processor = False
    if old_model_infos.tokenizer_class is not None:
        add_tokenizer = get_user_field(
            f"Do you want to create a new tokenizer? If `no`, it will use the same as {old_model_type} (y/n)?",
            convert_to=convert_to_bool,
            fallback_message="Please answer yes/no, y/n, true/false or 1/0. ",
        )
    if old_model_infos.fast_tokenizer_class is not None:
        add_fast_tokenizer = get_user_field(
            f"Do you want to create a new fast tokenizer? If `no`, it will use the same as {old_model_type} (y/n)?",
            convert_to=convert_to_bool,
            fallback_message="Please answer yes/no, y/n, true/false or 1/0. ",
        )
    if old_model_infos.image_processor_classes is not None:
        add_image_processor = get_user_field(
            f"Do you want to create a new image processor? If `no`, it will use the same as {old_model_type} (y/n)?",
            convert_to=convert_to_bool,
            fallback_message="Please answer yes/no, y/n, true/false or 1/0. ",
        )
    if old_model_infos.video_processor_class is not None:
        add_video_processor = get_user_field(
            f"Do you want to create a new video processor? If `no`, it will use the same as {old_model_type} (y/n)?",
            convert_to=convert_to_bool,
            fallback_message="Please answer yes/no, y/n, true/false or 1/0. ",
        )
    if old_model_infos.feature_extractor_class is not None:
        add_feature_extractor = get_user_field(
            f"Do you want to create a new feature extractor? If `no`, it will use the same as {old_model_type} (y/n)?",
            convert_to=convert_to_bool,
            fallback_message="Please answer yes/no, y/n, true/false or 1/0. ",
        )
    if old_model_infos.processor_class is not None:
        add_processor = get_user_field(
            f"Do you want to create a new processor? If `no`, it will use the same as {old_model_type} (y/n)?",
            convert_to=convert_to_bool,
            fallback_message="Please answer yes/no, y/n, true/false or 1/0. ",
        )

    old_lowercase_name = old_model_infos.lowercase_name
    # A list of the old filenames, along whether we should copy them or not
    filenames_to_add = (
        (f"configuration_{old_lowercase_name}.py", True),
        (f"modeling_{old_lowercase_name}.py", True),
        (f"tokenization_{old_lowercase_name}.py", add_tokenizer),
        (f"tokenization_{old_lowercase_name}_fast.py", add_fast_tokenizer),
        (f"image_processing_{old_lowercase_name}.py", add_image_processor),
        (f"video_processing_{old_lowercase_name}.py", add_video_processor),
        (f"feature_extraction_{old_lowercase_name}.py", add_feature_extractor),
        (f"processing_{old_lowercase_name}.py", add_processor),
    )

    return old_model_infos, new_lowercase_name, new_model_paper_name, filenames_to_add