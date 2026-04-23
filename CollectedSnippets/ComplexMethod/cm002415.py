def get_parameter_names(model, forbidden_layer_types, forbidden_layer_names=None):
    """
    Returns the names of the model parameters that are not inside a forbidden layer.
    """
    forbidden_layer_patterns = (
        [re.compile(pattern) for pattern in forbidden_layer_names] if forbidden_layer_names is not None else []
    )
    result = []
    for name, child in model.named_children():
        child_params = get_parameter_names(child, forbidden_layer_types, forbidden_layer_names)
        result += [
            f"{name}.{n}"
            for n in child_params
            if not isinstance(child, tuple(forbidden_layer_types))
            and not any(pattern.search(f"{name}.{n}".lower()) for pattern in forbidden_layer_patterns)
        ]
    # Add model specific parameters that are not in any child
    result += [
        k for k in model._parameters if not any(pattern.search(k.lower()) for pattern in forbidden_layer_patterns)
    ]

    return result