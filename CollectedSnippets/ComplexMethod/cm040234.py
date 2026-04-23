def _clone_sequential_model(model, clone_function, input_tensors=None):
    """Clone a `Sequential` model instance.

    Model cloning is similar to calling a model on new inputs,
    except that it creates new layers (and thus new weights) instead
    of sharing the weights of the existing layers.

    Args:
        model: Instance of `Sequential`.
        input_tensors: optional list of input tensors
            to build the model upon. If not provided,
            placeholders will be created.
        clone_function: callable to be applied on non-input layers in the model.
            By default, it clones the layer (without copying the weights).

    Returns:
        An instance of `Sequential` reproducing the behavior
        of the original model, on top of new inputs tensors,
        using newly instantiated weights.
    """

    if not isinstance(model, Sequential):
        raise ValueError(
            "Expected `model` argument "
            "to be a `Sequential` model instance. "
            f"Received: model={model}"
        )

    if not callable(clone_function):
        raise ValueError(
            "Expected `clone_function` argument to be a callable. "
            f"Received: clone_function={clone_function}"
        )

    new_layers = [clone_function(layer) for layer in model.layers]

    if isinstance(model._layers[0], InputLayer):
        ref_input_layer = model._layers[0]
        input_name = ref_input_layer.name
        input_batch_shape = ref_input_layer.batch_shape
        input_dtype = ref_input_layer._dtype
        input_optional = ref_input_layer.optional
    else:
        input_name = None
        input_dtype = None
        input_batch_shape = None
        input_optional = False

    if input_tensors is not None:
        if isinstance(input_tensors, (list, tuple)):
            if len(input_tensors) != 1:
                raise ValueError(
                    "Argument `input_tensors` must contain a single tensor."
                )
            input_tensors = input_tensors[0]
        if not isinstance(input_tensors, backend.KerasTensor):
            raise ValueError(
                "Argument `input_tensors` must be a KerasTensor. "
                f"Received invalid value: input_tensors={input_tensors}"
            )
        inputs = Input(
            tensor=input_tensors,
            name=input_name,
            optional=input_optional,
        )
        new_layers = [inputs] + new_layers
    else:
        if input_batch_shape is not None:
            inputs = Input(
                batch_shape=input_batch_shape,
                dtype=input_dtype,
                name=input_name,
                optional=input_optional,
            )
            new_layers = [inputs] + new_layers
    cloned_model = Sequential(
        new_layers, name=model.name, trainable=model.trainable
    )

    # If model compiled already then set same to cloned model
    if model.compiled:
        compiled_config = model.get_compile_config()
        cloned_model.compile_from_config(compiled_config)
    return cloned_model