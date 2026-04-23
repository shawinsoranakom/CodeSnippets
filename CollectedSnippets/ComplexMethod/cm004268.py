def getattribute_from_module(module, attr):
    if attr is None:
        return None
    if isinstance(attr, tuple):
        return tuple(getattribute_from_module(module, a) for a in attr)
    if isinstance(attr, dict):
        return {k: getattribute_from_module(module, v) for k, v in attr.items()}
    if hasattr(module, attr):
        return getattr(module, attr)
    # Some of the mappings have entries model_type -> object of another model type. In that case we try to grab the
    # object at the top level.
    transformers_module = importlib.import_module("transformers")

    if module != transformers_module:
        try:
            return getattribute_from_module(transformers_module, attr)
        except ValueError:
            raise ValueError(f"Could not find {attr} neither in {module} nor in {transformers_module}!")
    else:
        raise ValueError(f"Could not find {attr} in {transformers_module}!")