def get_frameworks_table() -> pd.DataFrame:
    """
    Generates a dataframe containing the supported auto classes for each model type, using the content of the auto
    modules.
    """
    # Dictionary model names to config.
    config_mapping_names = transformers_module.models.auto.configuration_auto.CONFIG_MAPPING_NAMES
    model_prefix_to_model_type = {
        config.replace("Config", ""): model_type for model_type, config in config_mapping_names.items()
    }

    pt_models = collections.defaultdict(bool)

    # Let's lookup through all transformers object (once) and find if models are supported by a given backend.
    for attr_name in dir(transformers_module):
        lookup_dict = None
        if _re_pt_models.match(attr_name) is not None:
            lookup_dict = pt_models
            attr_name = _re_pt_models.match(attr_name).groups()[0]

        if lookup_dict is not None:
            while len(attr_name) > 0:
                if attr_name in model_prefix_to_model_type:
                    lookup_dict[model_prefix_to_model_type[attr_name]] = True
                    break
                # Try again after removing the last word in the name
                attr_name = "".join(camel_case_split(attr_name)[:-1])

    all_models = set(pt_models.keys())
    all_models = list(all_models)
    all_models.sort()

    data = {"model_type": all_models}
    data["pytorch"] = [pt_models[t] for t in all_models]

    # Now let's find the right processing class for each model. In order we check if there is a Processor, then a
    # Tokenizer, then a FeatureExtractor, then an ImageProcessor
    processors = {}
    for t in all_models:
        if t in transformers_module.models.auto.processing_auto.PROCESSOR_MAPPING_NAMES:
            processors[t] = "AutoProcessor"
        elif t in transformers_module.models.auto.tokenization_auto.TOKENIZER_MAPPING_NAMES:
            processors[t] = "AutoTokenizer"
        elif t in transformers_module.models.auto.image_processing_auto.IMAGE_PROCESSOR_MAPPING_NAMES:
            processors[t] = "AutoImageProcessor"
        elif t in transformers_module.models.auto.feature_extraction_auto.FEATURE_EXTRACTOR_MAPPING_NAMES:
            processors[t] = "AutoFeatureExtractor"
        else:
            # Default to AutoTokenizer if a model has nothing, for backward compatibility.
            processors[t] = "AutoTokenizer"

    data["processor"] = [processors[t] for t in all_models]

    return pd.DataFrame(data)