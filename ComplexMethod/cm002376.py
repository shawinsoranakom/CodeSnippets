def check_config_attributes_being_used(config_class):
    """Check the arguments in `__init__` of `config_class` are used in the modeling files in the same directory

    Args:
        config_class (`type`):
            The configuration class for which the arguments in its `__init__` will be checked.
    """
    # Get the parameters in `__init__` of the configuration class, and the default values if any
    signature = dict(inspect.signature(config_class.__init__).parameters)
    parameter_names = [x for x in list(signature.keys()) if x not in ["self", "kwargs"]]
    parameter_defaults = [signature[param].default for param in parameter_names]

    # If `attribute_map` exists, an attribute can have different names to be used in the modeling files, and as long
    # as one variant is used, the test should pass
    reversed_attribute_map = {}
    if len(config_class.attribute_map) > 0:
        reversed_attribute_map = {v: k for k, v in config_class.attribute_map.items()}

    # Get the path to modeling source files
    config_source_file = inspect.getsourcefile(config_class)
    model_dir = os.path.dirname(config_source_file)
    modeling_paths = [os.path.join(model_dir, fn) for fn in os.listdir(model_dir) if fn.startswith("modeling_")]

    # Get the source code strings
    modeling_sources = []
    for path in modeling_paths:
        if os.path.isfile(path):
            with open(path, encoding="utf8") as fp:
                modeling_sources.append(fp.read())

    unused_attributes = []
    for config_param, default_value in zip(parameter_names, parameter_defaults):
        # `attributes` here is all the variant names for `config_param`
        attributes = [config_param]
        # some configuration classes have non-empty `attribute_map`, and both names could be used in the
        # corresponding modeling files. As long as one of them appears, it is fine.
        if config_param in reversed_attribute_map:
            attributes.append(reversed_attribute_map[config_param])

        if not check_attribute_being_used(config_class, attributes, default_value, modeling_sources):
            unused_attributes.append(attributes[0])

    return sorted(unused_attributes)