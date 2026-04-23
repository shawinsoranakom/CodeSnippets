def apply_patches():
    """
    Context manager to apply registered monkey patches within a block of code.

    This temporarily replaces original classes with their registered replacements during the execution of the block, and restores the original classes afterward.

    Example:
        ```python
        from transformers import Qwen2MoeModel, Qwen2MoeConfig
        from transformers.monkey_patching import register_patch_mapping, apply_patches

        # Register a patch
        register_patch_mapping(
            mapping={"Qwen2MoeExperts": CustomExperts}
        )

        # Apply patches within the context
        with apply_patches():
            # The model will use CustomExperts instead of Qwen2MoeExperts
            model = Qwen2MoeModel(Qwen2MoeConfig())

        # Outside the context, original classes are restored
        # The model will use Qwen2MoeExperts again
        model = Qwen2MoeModel(Qwen2MoeConfig())
        ```
    """
    mapping = get_patch_mapping()
    if not mapping:
        yield
        return

    original_classes = {}

    # Create list to avoid dict changed during iteration
    for module in list(sys.modules.values()):
        if module is None or not hasattr(module, "__name__"):
            continue
        if not module.__name__.startswith("transformers"):
            continue

        # Iterate through all attributes in transformers modules
        for attr_name in dir(module):
            # Check if this attribute name matches any pattern before accessing it
            replacement_class = _find_replacement_class(attr_name, mapping)
            if replacement_class is None:
                continue

            try:
                attr = getattr(module, attr_name)
                # Check if it's a class
                if not isinstance(attr, type):
                    continue

                original_classes[(module.__name__, attr_name)] = attr
                setattr(module, attr_name, replacement_class)
            except (AttributeError, TypeError, ImportError):
                # Skip attributes that can't be accessed or modules that can't be imported
                continue

    yield

    for (module_name, class_name), original_class in original_classes.items():
        module = sys.modules[module_name]
        setattr(module, class_name, original_class)