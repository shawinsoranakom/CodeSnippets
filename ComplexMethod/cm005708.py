def get_placeholders_dict(placeholders: set[str], model_name: str) -> Mapping[str, str | None]:
    """
    Get the dictionary of placeholders for the given model name.
    """
    # import here to avoid circular import
    from transformers.models import auto as auto_module

    placeholders_dict = {}
    for placeholder in placeholders:
        # Infer placeholders from the model name and the auto modules
        if placeholder in PLACEHOLDER_TO_AUTO_MODULE:
            try:
                place_holder_value = getattr(
                    getattr(auto_module, PLACEHOLDER_TO_AUTO_MODULE[placeholder][0]),
                    PLACEHOLDER_TO_AUTO_MODULE[placeholder][1],
                ).get(model_name, None)
            except ImportError:
                # In case a library is not installed, we don't want to fail the docstring generation
                place_holder_value = None
            if place_holder_value is not None:
                if isinstance(place_holder_value, list | tuple):
                    place_holder_value = (
                        place_holder_value[-1] if place_holder_value[-1] is not None else place_holder_value[0]
                    )
                placeholders_dict[placeholder] = place_holder_value if place_holder_value is not None else placeholder
            else:
                placeholders_dict[placeholder] = placeholder

    return placeholders_dict