def check_all_auto_mapping_names_in_config_mapping_names():
    """Check all keys defined in auto mappings (mappings of names) appear in `CONFIG_MAPPING_NAMES`."""
    # This is where we need to check we have all backends or the check is incomplete.
    check_missing_backends()

    failures = []
    # `TOKENIZER_PROCESSOR_MAPPING_NAMES` and `AutoTokenizer` is special, and don't need to follow the rule.
    mappings_to_check = {
        "IMAGE_PROCESSOR_MAPPING_NAMES": IMAGE_PROCESSOR_MAPPING_NAMES,
        "FEATURE_EXTRACTOR_MAPPING_NAMES": FEATURE_EXTRACTOR_MAPPING_NAMES,
        "PROCESSOR_MAPPING_NAMES": PROCESSOR_MAPPING_NAMES,
    }

    module = getattr(transformers.models.auto, "modeling_auto")
    # all mappings in a single auto modeling file
    mapping_names = [x for x in dir(module) if x.endswith("_MAPPING_NAMES")]
    mappings_to_check.update({name: getattr(module, name) for name in mapping_names})

    for name, mapping in mappings_to_check.items():
        for model_type in mapping:
            if model_type not in CONFIG_MAPPING_NAMES:
                failures.append(
                    f"`{model_type}` appears in the mapping `{name}` but it is not defined in the keys of "
                    "`CONFIG_MAPPING_NAMES`."
                )
    if len(failures) > 0:
        raise Exception(f"There were {len(failures)} failures:\n" + "\n".join(failures))