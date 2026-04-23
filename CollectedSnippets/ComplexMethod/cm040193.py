def load_weights_from_hdf5_group(f, model, skip_mismatch=False):
    """Implements topological (order-based) weight loading.

    Args:
        f: A pointer to a HDF5 group.
        model: Model instance.
        skip_mismatch: Boolean, whether to skip loading of weights
            where there is a mismatch in the shape of the weights,

    Raises:
        ValueError: in case of mismatch between provided layers
            and weights file.
    """
    if "keras_version" in f.attrs:
        original_keras_version = f.attrs["keras_version"]
        if hasattr(original_keras_version, "decode"):
            original_keras_version = original_keras_version.decode("utf8")
    else:
        original_keras_version = "1"
    if "backend" in f.attrs:
        original_backend = f.attrs["backend"]
        if hasattr(original_backend, "decode"):
            original_backend = original_backend.decode("utf8")
    else:
        original_backend = None

    filtered_layers = []
    for layer in model.layers:
        weights = _legacy_weights(layer)
        if weights:
            filtered_layers.append(layer)

    layer_names = load_attributes_from_hdf5_group(f, "layer_names")
    filtered_layer_names = []
    for name in layer_names:
        g = f[name]
        weight_names = load_attributes_from_hdf5_group(g, "weight_names")
        if weight_names:
            filtered_layer_names.append(name)
    layer_names = filtered_layer_names
    if len(layer_names) != len(filtered_layers):
        raise ValueError(
            "Layer count mismatch when loading weights from file. "
            f"Model expected {len(filtered_layers)} layers, found "
            f"{len(layer_names)} saved layers."
        )

    for k, name in enumerate(layer_names):
        g = f[name]
        layer = filtered_layers[k]
        symbolic_weights = _legacy_weights(layer)
        weight_values = load_subset_weights_from_hdf5_group(g)
        if len(weight_values) != len(symbolic_weights):
            raise ValueError(
                f"Weight count mismatch for layer #{k} (named {layer.name} in "
                f"the current model, {name} in the save file). "
                f"Layer expects {len(symbolic_weights)} weight(s). Received "
                f"{len(weight_values)} saved weight(s)"
            )
        _set_weights(
            layer,
            symbolic_weights,
            weight_values,
            skip_mismatch=skip_mismatch,
            name=f"layer #{k} (named {layer.name})",
        )

    if "top_level_model_weights" in f:
        symbolic_weights = list(
            # model.weights
            v
            for v in model._trainable_variables + model._non_trainable_variables
            if v in model.weights
        )
        weight_values = load_subset_weights_from_hdf5_group(
            f["top_level_model_weights"]
        )
        if len(weight_values) != len(symbolic_weights):
            raise ValueError(
                "Weight count mismatch for top-level weights when loading "
                "weights from file. "
                f"Model expects {len(symbolic_weights)} top-level weight(s). "
                f"Received {len(weight_values)} saved top-level weight(s)"
            )
        _set_weights(
            model,
            symbolic_weights,
            weight_values,
            skip_mismatch=skip_mismatch,
            name="top-level model",
        )