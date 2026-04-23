def check_config_attributes():
    """Check the arguments in `__init__` of all configuration classes are used in python files"""
    configs_with_unused_attributes = {}
    for _config_class in list(CONFIG_MAPPING.values()):
        # Skip deprecated models
        if "models.deprecated" in _config_class.__module__:
            continue
        # Some config classes are not in `CONFIG_MAPPING` (e.g. `CLIPVisionConfig`, `Blip2VisionConfig`, etc.)
        config_classes_in_module = [
            cls
            for name, cls in inspect.getmembers(
                inspect.getmodule(_config_class),
                lambda x: inspect.isclass(x)
                and issubclass(x, PreTrainedConfig)
                and inspect.getmodule(x) == inspect.getmodule(_config_class),
            )
        ]
        for config_class in config_classes_in_module:
            unused_attributes = check_config_attributes_being_used(config_class)
            if len(unused_attributes) > 0:
                configs_with_unused_attributes[config_class.__name__] = unused_attributes

    if len(configs_with_unused_attributes) > 0:
        error = "The following configuration classes contain unused attributes in the corresponding modeling files:\n"
        for name, attributes in configs_with_unused_attributes.items():
            error += f"{name}: {attributes}\n"

        raise ValueError(error)