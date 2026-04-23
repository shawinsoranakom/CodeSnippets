def load_weights_from_hdf5_group_by_name(f, model, skip_mismatch=False):
    """Implements name-based weight loading (instead of topological loading).

    Layers that have no matching name are skipped.

    Args:
        f: A pointer to a HDF5 group.
        model: Model instance.
        skip_mismatch: Boolean, whether to skip loading of layers
            where there is a mismatch in the number of weights,
            or a mismatch in the shape of the weights.

    Raises:
        ValueError: in case of mismatch between provided layers
            and weights file and skip_match=False.
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

    # New file format.
    layer_names = load_attributes_from_hdf5_group(f, "layer_names")

    # Reverse index of layer name to list of layers with name.
    index = {}
    for layer in model.layers:
        if layer.name:
            index.setdefault(layer.name, []).append(layer)

    for k, name in enumerate(layer_names):
        g = f[name]
        weight_values = load_subset_weights_from_hdf5_group(g)
        for layer in index.get(name, []):
            symbolic_weights = _legacy_weights(layer)
            if len(weight_values) != len(symbolic_weights):
                if skip_mismatch:
                    warnings.warn(
                        f"Skipping loading of weights for layer #{k} (named "
                        f"{layer.name}) due to mismatch in number of weights. "
                        f"Layer expects {len(symbolic_weights)} weight(s). "
                        f"Received {len(weight_values)} saved weight(s)",
                        stacklevel=2,
                    )
                    continue
                raise ValueError(
                    f"Weight count mismatch for layer #{k} "
                    f"(named {layer.name}). "
                    f"Layer expects {len(symbolic_weights)} weight(s). "
                    f"Received {len(weight_values)} saved weight(s)"
                )
            # Set values.
            _set_weights(
                layer,
                symbolic_weights,
                weight_values,
                skip_mismatch=skip_mismatch,
                name=f"layer #{k} (named {layer.name})",
            )

    if "top_level_model_weights" in f:
        symbolic_weights = (
            model._trainable_variables + model._non_trainable_variables
        )
        weight_values = load_subset_weights_from_hdf5_group(
            f["top_level_model_weights"]
        )

        if len(weight_values) != len(symbolic_weights):
            if skip_mismatch:
                warnings.warn(
                    "Skipping loading top-level weights for model due to "
                    "mismatch in number of weights. "
                    f"Model expects {len(symbolic_weights)} "
                    "top-level weight(s). "
                    f"Received {len(weight_values)} saved top-level weight(s)",
                    stacklevel=2,
                )
            else:
                raise ValueError(
                    "Weight count mismatch for top-level weights of model. "
                    f"Model expects {len(symbolic_weights)} "
                    "top-level weight(s). "
                    f"Received {len(weight_values)} saved top-level weight(s)"
                )
        else:
            _set_weights(
                model,
                symbolic_weights,
                weight_values,
                skip_mismatch=skip_mismatch,
                name="top-level model",
            )