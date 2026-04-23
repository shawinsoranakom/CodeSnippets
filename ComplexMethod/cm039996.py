def assert_input_compatibility(input_spec, inputs, layer_name):
    """Checks compatibility between the layer and provided inputs.

    This checks that the tensor(s) `inputs` verify the input assumptions
    of a layer (if any). If not, a clear and actional exception gets raised.

    Args:
        input_spec: An InputSpec instance, list of InputSpec instances, a nested
            structure of InputSpec instances, or None.
        inputs: Input tensor, list of input tensors, or a nested structure of
            input tensors.
        layer_name: String, name of the layer (for error message formatting).

    Raises:
        ValueError: in case of mismatch between
            the provided inputs and the expectations of the layer.
    """
    if not input_spec:
        return

    input_spec = tree.flatten(input_spec)
    if isinstance(inputs, dict):
        # Flatten `inputs` by reference order if input spec names are provided
        names = [spec.name for spec in input_spec]
        if all(names):
            list_inputs = []
            for name in names:
                if name not in inputs:
                    raise ValueError(
                        f'Missing data for input "{name}". '
                        "You passed a data dictionary with keys "
                        f"{list(inputs.keys())}. "
                        f"Expected the following keys: {names}"
                    )
                list_inputs.append(inputs[name])
            inputs = list_inputs

    inputs = tree.flatten(inputs)
    if len(inputs) != len(input_spec):
        raise ValueError(
            f'Layer "{layer_name}" expects {len(input_spec)} input(s),'
            f" but it received {len(inputs)} input tensors. "
            f"Inputs received: {inputs}"
        )
    for input_index, (x, spec) in enumerate(zip(inputs, input_spec)):
        if spec is None:
            continue
        if x is None and spec.optional:
            continue

        # Having a shape/dtype is the only commonality of the various
        # tensor-like objects that may be passed. The most common kind of
        # invalid type we are guarding for is a Layer instance (Functional API),
        # which does not have a `shape` attribute.
        if not hasattr(x, "shape"):
            raise ValueError(
                f"Inputs to a layer should be tensors. Got '{x}' "
                f"(of type {type(x)}) as input for layer '{layer_name}'."
            )

        shape = backend.standardize_shape(x.shape)
        ndim = len(shape)
        # Check ndim.
        if spec.ndim is not None and not spec.allow_last_axis_squeeze:
            if ndim != spec.ndim:
                raise ValueError(
                    f"Input {input_index} with name '{spec.name}' of layer "
                    f"'{layer_name}' is incompatible with the layer: "
                    f"expected ndim={spec.ndim}, found ndim={ndim}. "
                    f"Full shape received: {shape}"
                )
        if spec.max_ndim is not None:
            if ndim is not None and ndim > spec.max_ndim:
                raise ValueError(
                    f"Input {input_index} with name '{spec.name}' of layer "
                    f"'{layer_name}' is incompatible with the layer: "
                    f"expected max_ndim={spec.max_ndim}, "
                    f"found ndim={ndim}"
                )
        if spec.min_ndim is not None:
            if ndim is not None and ndim < spec.min_ndim:
                raise ValueError(
                    f"Input {input_index} with name '{spec.name}' of layer "
                    f"'{layer_name}' is incompatible with the layer: "
                    f"expected min_ndim={spec.min_ndim}, "
                    f"found ndim={ndim}. "
                    f"Full shape received: {shape}"
                )
        # Check dtype.
        if spec.dtype is not None:
            dtype = backend.standardize_dtype(x.dtype)
            if dtype != spec.dtype:
                raise ValueError(
                    f"Input {input_index} with name '{spec.name}' of layer "
                    f"'{layer_name}' is incompatible with the layer: "
                    f"expected dtype={spec.dtype}, "
                    f"found dtype={dtype}"
                )

        # Check specific shape axes.
        if spec.axes:
            for axis, value in spec.axes.items():
                if value is not None and shape[axis] not in {
                    value,
                    None,
                }:
                    raise ValueError(
                        f"Input {input_index} with name '{spec.name}' of layer "
                        f"'{layer_name}' is incompatible with the layer: "
                        f"expected axis {axis} of input shape to have value "
                        f"{value}, but received input with shape {shape}"
                    )
        # Check shape.
        if spec.shape is not None:
            spec_shape = spec.shape
            if spec.allow_last_axis_squeeze:
                if shape and shape[-1] == 1:
                    shape = shape[:-1]
                if spec_shape and spec_shape[-1] == 1:
                    spec_shape = spec_shape[:-1]
            for spec_dim, dim in zip(spec_shape, shape):
                if spec_dim is not None and dim is not None:
                    if spec_dim != dim:
                        raise ValueError(
                            f"Input {input_index} with name '{spec.name}' of "
                            f"layer '{layer_name}' is incompatible with the "
                            f"layer: expected shape={spec.shape}, found "
                            f"shape={shape}"
                        )