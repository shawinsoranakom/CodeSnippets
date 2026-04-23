def model_to_dot(
    model,
    show_shapes=False,
    show_dtype=False,
    show_layer_names=True,
    rankdir="TB",
    expand_nested=False,
    dpi=200,
    subgraph=False,
    show_layer_activations=False,
    show_trainable=False,
    splines="ortho",
    **kwargs,
):
    """Convert a Keras model to dot format.

    Args:
        model: A Keras model instance.
        show_shapes: whether to display shape information.
        show_dtype: whether to display layer dtypes.
        show_layer_names: whether to display layer names.
        rankdir: `rankdir` argument passed to PyDot,
            a string specifying the format of the plot: `"TB"`
            creates a vertical plot; `"LR"` creates a horizontal plot.
        expand_nested: whether to expand nested Functional models
            into clusters.
        dpi: Image resolution in dots per inch.
        subgraph: whether to return a `pydot.Cluster` instance.
        show_layer_activations: Display layer activations (only for layers that
            have an `activation` property).
        show_trainable: whether to display if a layer is trainable.
        splines: Controls how edges are drawn. Defaults to `"ortho"`
            (right-angle lines). Other options include `"curved"`,
            `"polyline"`, `"spline"`, and `"line"`.

    Returns:
        A `pydot.Dot` instance representing the Keras model or
        a `pydot.Cluster` instance representing nested model if
        `subgraph=True`.
    """
    from keras.src.ops.function import make_node_key

    if not model.built:
        raise ValueError(
            "This model has not yet been built. "
            "Build the model first by calling `build()` or by calling "
            "the model on a batch of data."
        )

    from keras.src.models import functional
    from keras.src.models import sequential

    # from keras.src.layers import Wrapper

    if not check_pydot():
        raise ImportError(
            "You must install pydot (`pip install pydot`) for "
            "model_to_dot to work."
        )

    if subgraph:
        dot = pydot.Cluster(style="dashed", graph_name=model.name)
        dot.set("label", model.name)
        dot.set("labeljust", "l")
    else:
        dot = pydot.Dot()
        dot.set("rankdir", rankdir)
        dot.set("concentrate", True)
        dot.set("dpi", dpi)
        dot.set("splines", splines)
        dot.set_node_defaults(shape="record")

    if kwargs.pop("layer_range", None) is not None:
        raise ValueError("Argument `layer_range` is no longer supported.")
    if kwargs:
        raise ValueError(f"Unrecognized keyword arguments: {kwargs}")

    kwargs = {
        "show_layer_names": show_layer_names,
        "show_layer_activations": show_layer_activations,
        "show_dtype": show_dtype,
        "show_shapes": show_shapes,
        "show_trainable": show_trainable,
    }

    if isinstance(model, sequential.Sequential):
        layers = model.layers
    elif not isinstance(model, functional.Functional):
        # We treat subclassed models as a single node.
        node = make_node(model, **kwargs)
        dot.add_node(node)
        return dot
    else:
        layers = model._operations

    # Create graph nodes.
    for i, layer in enumerate(layers):
        # Process nested functional and sequential models.
        if expand_nested and isinstance(
            layer, (functional.Functional, sequential.Sequential)
        ):
            submodel = model_to_dot(
                layer,
                show_shapes,
                show_dtype,
                show_layer_names,
                rankdir,
                expand_nested,
                subgraph=True,
                show_layer_activations=show_layer_activations,
                show_trainable=show_trainable,
            )
            dot.add_subgraph(submodel)

        else:
            node = make_node(layer, **kwargs)
            dot.add_node(node)

    # Connect nodes with edges.
    if isinstance(model, sequential.Sequential):
        if not expand_nested:
            # Single Sequential case.
            for i in range(len(layers) - 1):
                add_edge(dot, layers[i], layers[i + 1])
            return dot
        else:
            # The first layer is connected to the `InputLayer`, which is not
            # represented for Sequential models, so we skip it. What will draw
            # the incoming edge from outside of the sequential model is the
            # edge connecting the Sequential model itself.
            layers = model.layers[1:]

    # Functional and nested Sequential case.
    for layer in layers:
        # Go from current layer to input `Node`s.
        for inbound_index, inbound_node in enumerate(layer._inbound_nodes):
            # `inbound_node` is a `Node`.
            if (
                isinstance(model, functional.Functional)
                and make_node_key(layer, inbound_index) not in model._nodes
            ):
                continue

            # Go from input `Node` to `KerasTensor` representing that input.
            for input_index, input_tensor in enumerate(
                inbound_node.input_tensors
            ):
                # `input_tensor` is a `KerasTensor`.
                # `input_history` is a `KerasHistory`.
                input_history = input_tensor._keras_history
                if input_history.operation is None:
                    # Operation is `None` for `Input` tensors.
                    continue

                # Go from input `KerasTensor` to the `Operation` that produced
                # it as an output.
                input_node = input_history.operation._inbound_nodes[
                    input_history.node_index
                ]
                output_index = input_history.tensor_index

                # Tentative source and destination of the edge.
                source = input_node.operation
                destination = layer

                if not expand_nested:
                    # No nesting, connect directly.
                    add_edge(dot, source, layer)
                    continue

                # ==== Potentially nested models case ====

                # ---- Resolve the source of the edge ----
                while isinstance(
                    source,
                    (functional.Functional, sequential.Sequential),
                ):
                    # When `source` is a `Functional` or `Sequential` model, we
                    # need to connect to the correct box within that model.
                    # Functional and sequential models do not have explicit
                    # "output" boxes, so we need to find the correct layer that
                    # produces the output we're connecting to, which can be
                    # nested several levels deep in sub-models. Hence the while
                    # loop to continue going into nested models until we
                    # encounter a real layer that's not a `Functional` or
                    # `Sequential`.
                    source, _, output_index = source.outputs[
                        output_index
                    ]._keras_history

                # ---- Resolve the destination of the edge ----
                while isinstance(
                    destination,
                    (functional.Functional, sequential.Sequential),
                ):
                    if isinstance(destination, functional.Functional):
                        # When `destination` is a `Functional`, we point to the
                        # specific `InputLayer` in the model.
                        destination = destination.inputs[
                            input_index
                        ]._keras_history.operation
                    else:
                        # When `destination` is a `Sequential`, there is no
                        # explicit "input" box, so we want to point to the first
                        # box in the model, but it may itself be another model.
                        # Hence the while loop to continue going into nested
                        # models until we encounter a real layer that's not a
                        # `Functional` or `Sequential`.
                        destination = destination.layers[0]

                add_edge(dot, source, destination)
    return dot