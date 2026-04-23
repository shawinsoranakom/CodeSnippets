def _export_onnx_jax(model, filepath, input_signature, opset_version):
    """Export a JAX-backend Keras model to ONNX using jax2onnx.

    Converts the model directly from JAX to ONNX without going through
    TensorFlow, avoiding the deprecated jax2tf options (``enable_xla``
    and ``native_serialization``).
    """
    import jax
    import numpy as np

    from keras.src.utils.module_utils import jax2onnx

    # Flatten specs from the (possibly nested) input_signature.
    flat_specs = tree.flatten(input_signature)

    # Build input names from the flat specs.
    flat_input_names = [
        getattr(spec, "name", None) or f"input_{i}"
        for i, spec in enumerate(flat_specs)
    ]

    # Convert Keras InputSpecs to jax2onnx-compatible input descriptors
    # with string names for dynamic (None) dimensions.
    jax_inputs = []
    for i, spec in enumerate(flat_specs):
        shape = []
        for dim_idx, dim in enumerate(spec.shape):
            if dim is None:
                shape.append("batch" if dim_idx == 0 else f"dim_{i}_{dim_idx}")
            else:
                shape.append(dim)
        jax_inputs.append(
            jax.ShapeDtypeStruct(tuple(shape), np.dtype(spec.dtype))
        )

    # Wrapper that restructures flat positional args back into whatever
    # nested form the model expects (single tensor, list, tuple, dict).
    def predict_fn(*flat_args):
        args = tree.pack_sequence_as(input_signature, flat_args)
        if len(args) == 1:
            return model(args[0], training=False)
        return model(*args, training=False)

    export_kwargs = {
        "input_names": flat_input_names,
        "return_mode": "file",
        "output_path": str(filepath),
    }
    if opset_version is not None:
        export_kwargs["opset"] = opset_version

    jax2onnx.to_onnx(predict_fn, inputs=jax_inputs, **export_kwargs)