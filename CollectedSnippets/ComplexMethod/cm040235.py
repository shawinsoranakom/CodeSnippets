def _clone_functional_model(
    model, clone_function, input_tensors=None, call_function=None
):
    """Clone a `Functional` model instance.

    Model cloning is similar to calling a model on new inputs,
    except that it creates new layers (and thus new weights) instead
    of sharing the weights of the existing layers.

    Input layers are always cloned.

    Args:
        model: Instance of `Functional`.
        input_tensors: optional list of input tensors
            to build the model upon. If not provided,
            placeholders will be created.
        clone_function: callable to be applied on non-input layers in the model.
            By default, it clones the layer (without copying the weights).

    Returns:
        An instance of `Functional` reproducing the behavior
        of the original model, on top of new inputs tensors,
        using newly instantiated weights.
    """

    if not callable(clone_function):
        raise ValueError(
            "Expected `clone_function` argument to be a callable. "
            f"Received: clone_function={clone_function}"
        )

    if not isinstance(model, Functional):
        raise ValueError(
            "Expected `model` argument "
            f"to be a Functional Model instance. Received: model={model}"
        )

    if input_tensors is not None:
        if not all(
            isinstance(x, backend.KerasTensor)
            for x in tree.flatten(input_tensors)
        ):
            raise ValueError(
                "All entries in `input_tensors` must be KerasTensors. "
                f"Received invalid values: inputs_tensors={input_tensors}"
            )
        try:
            tree.assert_same_structure(input_tensors, model.input)
        except ValueError as e:
            raise ValueError(
                "`input_tensors` must have the same structure as model.input"
                f"\nReference structure: {model.input}"
                f"\nReceived structure: {input_tensors}"
            ) from e
    else:
        input_tensors = tree.map_structure(
            lambda x: Input(batch_shape=x.shape, dtype=x.dtype, name=x.name),
            model.input,
        )

    def operation_fn(layer):
        new_layer = clone_function(layer)
        return new_layer

    output_tensors = model._run_through_graph(
        input_tensors,
        operation_fn=operation_fn,
        call_fn=call_function,
    )

    if functional_like_constructor(model.__class__):
        new_model = model.__class__(
            input_tensors, output_tensors, name=model.name
        )
    else:
        # This may be incorrect: the new model will end up having a different
        # class than the original. However various existing models rely
        # on this behavior, so we keep it.
        new_model = Functional(input_tensors, output_tensors, name=model.name)
    if model.compiled:
        compiled_config = model.get_compile_config()
        new_model.compile_from_config(compiled_config)
    return new_model