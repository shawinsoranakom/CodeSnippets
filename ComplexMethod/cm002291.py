def get_all_model_names():
    model_names = set()

    module_name = "modeling_auto"
    module = getattr(transformers.models.auto, module_name, None)
    if module is not None:
        # all mappings in a single auto modeling file
        mapping_names = [x for x in dir(module) if x.endswith("_MAPPING_NAMES") and x.startswith("MODEL_")]
        for name in mapping_names:
            mapping = getattr(module, name)
            if mapping is not None:
                for v in mapping.values():
                    if isinstance(v, (list, tuple)):
                        model_names.update(v)
                    elif isinstance(v, str):
                        model_names.add(v)

    return sorted(model_names)