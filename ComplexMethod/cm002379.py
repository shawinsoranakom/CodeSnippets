def get_architectures_from_config_class(config_class, arch_mappings, models_to_skip=None):
    """Return a tuple of all possible architectures attributed to a configuration class `config_class`.

    For example, BertConfig -> [BertModel, BertForMaskedLM, ..., BertForQuestionAnswering].
    """
    # A model architecture could appear in several mappings. For example, `BartForConditionalGeneration` is in
    #   - MODEL_FOR_PRETRAINING_MAPPING_NAMES
    #   - MODEL_FOR_MASKED_LM_MAPPING_NAMES
    #   - MODEL_FOR_SEQ_TO_SEQ_CAUSAL_LM_MAPPING_NAMES
    # We avoid the duplication.
    architectures = set()

    if models_to_skip is None:
        models_to_skip = []
    models_to_skip = UNCONVERTIBLE_MODEL_ARCHITECTURES.union(models_to_skip)

    for mapping in arch_mappings:
        if config_class in mapping:
            try:
                models = mapping[config_class]
            except ValueError as e:
                # Extract missing model name from error message
                match = re.search(r"Could not find (\w+)", str(e))
                missing_model_name = match.group(1) if match else None

                # Get the package module from config_class
                module_path = config_class.__module__.rsplit(".", 1)[0]  # e.g. 'transformers.models.voxtral_realtime'
                module = importlib.import_module(module_path)

                # Find modeling_* submodule names
                modeling_names = [name for name in dir(module) if name.startswith("modeling_")]

                models = ()
                for modeling_name in modeling_names:
                    modeling_module = getattr(module, modeling_name)
                    _models = getattr(modeling_module, missing_model_name, None)
                    if _models is not None:
                        models = _models
                        break

            models = tuple(models) if isinstance(models, collections.abc.Sequence) else (models,)
            for model in models:
                if model.__name__ not in models_to_skip:
                    architectures.add(model)

    architectures = tuple(architectures)

    return architectures