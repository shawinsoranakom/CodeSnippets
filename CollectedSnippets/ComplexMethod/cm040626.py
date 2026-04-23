def plot_model(
    model,
    to_file="model.png",
    show_shapes=False,
    show_dtype=False,
    show_layer_names=False,
    rankdir="TB",
    expand_nested=False,
    dpi=200,
    show_layer_activations=False,
    show_trainable=False,
    splines="ortho",
    **kwargs,
):
    """Converts a Keras model to dot format and save to a file.

    Example:

    ```python
    inputs = ...
    outputs = ...
    model = keras.Model(inputs=inputs, outputs=outputs)

    dot_img_file = '/tmp/model_1.png'
    keras.utils.plot_model(model, to_file=dot_img_file, show_shapes=True)
    ```

    Args:
        model: A Keras model instance
        to_file: File name of the plot image.
        show_shapes: whether to display shape information.
        show_dtype: whether to display layer dtypes.
        show_layer_names: whether to display layer names.
        rankdir: `rankdir` argument passed to PyDot,
            a string specifying the format of the plot: `"TB"`
            creates a vertical plot; `"LR"` creates a horizontal plot.
        expand_nested: whether to expand nested Functional models
            into clusters.
        dpi: Image resolution in dots per inch.
        show_layer_activations: Display layer activations (only for layers that
            have an `activation` property).
        show_trainable: whether to display if a layer is trainable.
        splines: Controls how edges are drawn. Defaults to `"ortho"`
            (right-angle lines). Other options include `"curved"`,
            `"polyline"`, `"spline"`, and `"line"`.

    Returns:
        A Jupyter notebook Image object if Jupyter is installed.
        This enables in-line display of the model plots in notebooks.
    """

    if not model.built:
        raise ValueError(
            "This model has not yet been built. "
            "Build the model first by calling `build()` or by calling "
            "the model on a batch of data."
        )
    if not check_pydot():
        message = (
            "You must install pydot (`pip install pydot`) "
            "for `plot_model` to work."
        )
        if "IPython.core.magics.namespace" in sys.modules:
            # We don't raise an exception here in order to avoid crashing
            # notebook tests where graphviz is not available.
            io_utils.print_msg(message)
            return
        else:
            raise ImportError(message)
    if not check_graphviz():
        message = (
            "You must install graphviz "
            "(see instructions at https://graphviz.gitlab.io/download/) "
            "for `plot_model` to work."
        )
        if "IPython.core.magics.namespace" in sys.modules:
            # We don't raise an exception here in order to avoid crashing
            # notebook tests where graphviz is not available.
            io_utils.print_msg(message)
            return
        else:
            raise ImportError(message)

    if kwargs.pop("layer_range", None) is not None:
        raise ValueError("Argument `layer_range` is no longer supported.")
    if kwargs:
        raise ValueError(f"Unrecognized keyword arguments: {kwargs}")

    dot = model_to_dot(
        model,
        show_shapes=show_shapes,
        show_dtype=show_dtype,
        show_layer_names=show_layer_names,
        rankdir=rankdir,
        expand_nested=expand_nested,
        dpi=dpi,
        show_layer_activations=show_layer_activations,
        show_trainable=show_trainable,
        splines=splines,
    )
    to_file = str(to_file)
    if dot is None:
        return
    _, extension = os.path.splitext(to_file)
    if not extension:
        extension = "png"
    else:
        extension = extension[1:]
    # Save image to disk.
    dot.write(to_file, format=extension)
    # Return the image as a Jupyter Image object, to be displayed in-line.
    # Note that we cannot easily detect whether the code is running in a
    # notebook, and thus we always return the Image if Jupyter is available.
    if extension != "pdf":
        try:
            from IPython import display

            return display.Image(filename=to_file)
        except ImportError:
            pass