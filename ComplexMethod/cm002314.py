def check_all_auto_object_names_being_defined():
    """Check all names defined in auto (name) mappings exist in the library."""
    # This is where we need to check we have all backends or the check is incomplete.
    check_missing_backends()

    failures = []
    mappings_to_check = {
        "TOKENIZER_MAPPING_NAMES": TOKENIZER_MAPPING_NAMES,
        "IMAGE_PROCESSOR_MAPPING_NAMES": IMAGE_PROCESSOR_MAPPING_NAMES,
        "FEATURE_EXTRACTOR_MAPPING_NAMES": FEATURE_EXTRACTOR_MAPPING_NAMES,
        "PROCESSOR_MAPPING_NAMES": PROCESSOR_MAPPING_NAMES,
    }

    module = getattr(transformers.models.auto, "modeling_auto")
    # all mappings in a single auto modeling file
    mapping_names = [x for x in dir(module) if x.endswith("_MAPPING_NAMES")]
    mappings_to_check.update({name: getattr(module, name) for name in mapping_names})

    for name, mapping in mappings_to_check.items():
        for class_names in mapping.values():
            if isinstance(class_names, dict):
                class_names = tuple(class_names.values())
            if not isinstance(class_names, tuple):
                class_names = (class_names,)
            for class_name in class_names:
                if class_name is None:
                    continue
                # dummy object is accepted
                if not hasattr(transformers, class_name):
                    # If the class name is in a model name mapping, let's not check if there is a definition in any modeling
                    # module, if it's a private model defined in this file.
                    if name.endswith("MODEL_MAPPING_NAMES") and is_a_private_model(class_name):
                        continue
                    if name.endswith("MODEL_FOR_IMAGE_MAPPING_NAMES") and is_a_private_model(class_name):
                        continue
                    failures.append(
                        f"`{class_name}` appears in the mapping `{name}` but it is not defined in the library."
                    )
    if len(failures) > 0:
        raise Exception(f"There were {len(failures)} failures:\n" + "\n".join(failures))