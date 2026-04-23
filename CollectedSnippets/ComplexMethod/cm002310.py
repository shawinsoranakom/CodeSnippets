def get_models(module: types.ModuleType, include_pretrained: bool = False) -> list[tuple[str, type]]:
    """
    Get the objects in a module that are models.

    Args:
        module (`types.ModuleType`):
            The module from which we are extracting models.
        include_pretrained (`bool`, *optional*, defaults to `False`):
            Whether or not to include the `PreTrainedModel` subclass (like `BertPreTrainedModel`) or not.

    Returns:
        List[Tuple[str, type]]: List of models as tuples (class name, actual class).
    """
    models = []
    for attr_name in dir(module):
        if not include_pretrained and ("Pretrained" in attr_name or "PreTrained" in attr_name):
            continue
        attr = getattr(module, attr_name)
        if (
            isinstance(attr, type)
            and issubclass(attr, transformers.PreTrainedModel)
            and attr.__module__ == module.__name__
        ):
            models.append((attr_name, attr))
    return models