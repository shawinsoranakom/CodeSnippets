def main(overwrite: bool):
    filename = "src/transformers/models/auto/auto_mappings.py"

    # 1. Read existing file content if available
    old_content = ""
    if os.path.exists(filename):
        old_content = open(filename, "r").read()

    # 2. Generate new config mapping dicts by parsing all model-config classes
    config_mapping, special_mapping = build_config_mapping_names()
    image_processor_mapping = build_image_processor_mapping(config_mapping=config_mapping)
    video_processor_mapping = build_video_processor_mapping(config_mapping=config_mapping)

    # Make sure users aren't duplicating the same keys manually
    check_duplicates(MISSING_IMAGE_PROCESSOR_MAPPING_NAMES, image_processor_mapping)
    check_duplicates(MISSING_VIDEO_PROCESSOR_MAPPING_NAMES, video_processor_mapping)

    # The config mapping has to be one-to-one for correct `AutoConfig.from_pretrained()` because `LazyMapping`
    # reverts keys/values and creates a dict from it. Duplicate values will be overwritten by whatever comes at last
    duplicate_keys = [n for n, c in Counter(COMPLETE_CONFIG_MAPPING_NAMES.keys()).items() if c > 1]
    if duplicate_keys:
        raise ValueError(
            f"Keys in `CONFIG_MAPPING_NAMES` contain duplicates = {duplicate_keys}. "
            "The mapping has to be one-to-one to ensure correct `AutoConfig` functionality!"
        )

    duplicate_values = [
        n
        for n, c in Counter(COMPLETE_CONFIG_MAPPING_NAMES.values()).items()
        if c > 1 and n not in IGNORE_DUPLICATE_CONFIG
    ]
    if duplicate_values:
        raise ValueError(
            f"Values in `CONFIG_MAPPING_NAMES` contain duplicates = {duplicate_values}. "
            "The mapping has to be one-to-one to ensure correct `AutoConfig` functionality!"
        )

    new_mappings = {
        "CONFIG_MAPPING_NAMES": config_mapping,
        "SPECIAL_MODEL_TYPE_TO_MODULE_NAME": special_mapping,
        "IMAGE_PROCESSOR_MAPPING_NAMES": image_processor_mapping,
        "VIDEO_PROCESSOR_MAPPING_NAMES": video_processor_mapping,
    }
    new_content = AUTO_GENERATED_HADER + "\nfrom collections import OrderedDict\n\n"
    for k, v in new_mappings.items():
        new_content += format_ordered_dict(name=k, data=v)

    # 3. If the new auto-generate content is different, overwrite it
    # Dirty hack to sort and apply ruff to the file content, for easier matching
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py") as tmpfile:
        tmpfile.write(new_content)
        tmpfile_path = tmpfile.name

        run_ruff_and_sort(tmpfile_path)
        new_content = open(tmpfile_path, "r").read()

    if old_content != new_content:
        if not overwrite:
            raise Exception(
                "Generated auto-mapping is not consistent with the contents of `models/auto/auto_mappings.py`:\n"
                + "\nRun `make fix-repo` or `python utils/check_auto.py --fix_and_overwrite` to fix them."
            )
        else:
            with open(filename, "w") as f:
                f.write(new_content)