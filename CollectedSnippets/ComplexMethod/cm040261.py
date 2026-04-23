def MobileNetV3(
    stack_fn,
    last_point_ch,
    input_shape=None,
    alpha=1.0,
    model_type="large",
    minimalistic=False,
    include_top=True,
    weights="imagenet",
    input_tensor=None,
    classes=1000,
    pooling=None,
    dropout_rate=0.2,
    classifier_activation="softmax",
    include_preprocessing=True,
    name=None,
):
    if not (weights in {"imagenet", None} or file_utils.exists(weights)):
        raise ValueError(
            "The `weights` argument should be either "
            "`None` (random initialization), `imagenet` "
            "(pre-training on ImageNet), "
            "or the path to the weights file to be loaded.  "
            f"Received weights={weights}"
        )

    if weights == "imagenet" and include_top and classes != 1000:
        raise ValueError(
            'If using `weights="imagenet"` with `include_top` '
            "as true, `classes` should be 1000.  "
            f"Received classes={classes}"
        )

    # Determine proper input shape and default size.
    # If both input_shape and input_tensor are used, they should match
    if input_shape is not None and input_tensor is not None:
        try:
            is_input_t_tensor = backend.is_keras_tensor(input_tensor)
        except ValueError:
            try:
                is_input_t_tensor = backend.is_keras_tensor(
                    operation_utils.get_source_inputs(input_tensor)
                )
            except ValueError:
                raise ValueError(
                    "input_tensor: ",
                    input_tensor,
                    "is not type input_tensor.  "
                    f"Received type(input_tensor)={type(input_tensor)}",
                )
        if is_input_t_tensor:
            if backend.image_data_format() == "channels_first":
                if input_tensor.shape[1] != input_shape[1]:
                    raise ValueError(
                        "When backend.image_data_format()=channels_first, "
                        "input_shape[1] must equal "
                        "input_tensor.shape[1].  Received "
                        f"input_shape={input_shape}, "
                        "input_tensor.shape="
                        f"{input_tensor.shape}"
                    )
            else:
                if input_tensor.shape[2] != input_shape[1]:
                    raise ValueError(
                        "input_shape[1] must equal "
                        "input_tensor.shape[2].  Received "
                        f"input_shape={input_shape}, "
                        "input_tensor.shape="
                        f"{input_tensor.shape}"
                    )
        else:
            raise ValueError(
                "input_tensor specified: ",
                input_tensor,
                "is not a keras tensor",
            )

    # If input_shape is None, infer shape from input_tensor
    if input_shape is None and input_tensor is not None:
        try:
            backend.is_keras_tensor(input_tensor)
        except ValueError:
            raise ValueError(
                "input_tensor: ",
                input_tensor,
                "is type: ",
                type(input_tensor),
                "which is not a valid type",
            )

        if backend.is_keras_tensor(input_tensor):
            if backend.image_data_format() == "channels_first":
                rows = input_tensor.shape[2]
                cols = input_tensor.shape[3]
                input_shape = (3, cols, rows)
            else:
                rows = input_tensor.shape[1]
                cols = input_tensor.shape[2]
                input_shape = (cols, rows, 3)
    # If input_shape is None and input_tensor is None using standard shape
    if input_shape is None and input_tensor is None:
        if backend.image_data_format() == "channels_last":
            input_shape = (None, None, 3)
        else:
            input_shape = (3, None, None)

    if backend.image_data_format() == "channels_last":
        row_axis, col_axis = (0, 1)
    else:
        row_axis, col_axis = (1, 2)
    rows = input_shape[row_axis]
    cols = input_shape[col_axis]
    if rows and cols and (rows < 32 or cols < 32):
        raise ValueError(
            "Input size must be at least 32x32; Received `input_shape="
            f"{input_shape}`"
        )
    if weights == "imagenet":
        if (
            not minimalistic
            and alpha not in [0.75, 1.0]
            or minimalistic
            and alpha != 1.0
        ):
            raise ValueError(
                "If imagenet weights are being loaded, "
                "alpha can be one of `0.75`, `1.0` for non minimalistic "
                "or `1.0` for minimalistic only."
            )

        if rows != cols or rows != 224:
            warnings.warn(
                "`input_shape` is undefined or non-square, "
                "or `rows` is not 224. "
                "Weights for input shape (224, 224) will be "
                "loaded as the default.",
                stacklevel=2,
            )

    if input_tensor is None:
        img_input = layers.Input(shape=input_shape)
    else:
        if not backend.is_keras_tensor(input_tensor):
            img_input = layers.Input(tensor=input_tensor, shape=input_shape)
        else:
            img_input = input_tensor

    channel_axis = 1 if backend.image_data_format() == "channels_first" else -1

    if minimalistic:
        kernel = 3
        activation = relu
        se_ratio = None
    else:
        kernel = 5
        activation = hard_swish
        se_ratio = 0.25

    x = img_input
    if include_preprocessing:
        x = layers.Rescaling(scale=1.0 / 127.5, offset=-1.0)(x)
    x = layers.Conv2D(
        16,
        kernel_size=3,
        strides=(2, 2),
        padding="same",
        use_bias=False,
        name="conv",
    )(x)
    x = layers.BatchNormalization(
        axis=channel_axis, epsilon=1e-3, momentum=0.999, name="conv_bn"
    )(x)
    x = activation(x)

    x = stack_fn(x, kernel, activation, se_ratio)

    last_conv_ch = _depth(x.shape[channel_axis] * 6)

    # if the width multiplier is greater than 1 we
    # increase the number of output channels
    if alpha > 1.0:
        last_point_ch = _depth(last_point_ch * alpha)
    x = layers.Conv2D(
        last_conv_ch,
        kernel_size=1,
        padding="same",
        use_bias=False,
        name="conv_1",
    )(x)
    x = layers.BatchNormalization(
        axis=channel_axis, epsilon=1e-3, momentum=0.999, name="conv_1_bn"
    )(x)
    x = activation(x)
    if include_top:
        x = layers.GlobalAveragePooling2D(keepdims=True)(x)
        x = layers.Conv2D(
            last_point_ch,
            kernel_size=1,
            padding="same",
            use_bias=True,
            name="conv_2",
        )(x)
        x = activation(x)

        if dropout_rate > 0:
            x = layers.Dropout(dropout_rate)(x)
        x = layers.Conv2D(
            classes, kernel_size=1, padding="same", name="logits"
        )(x)
        x = layers.Flatten()(x)
        imagenet_utils.validate_activation(classifier_activation, weights)
        x = layers.Activation(
            activation=classifier_activation, name="predictions"
        )(x)
    else:
        if pooling == "avg":
            x = layers.GlobalAveragePooling2D(name="avg_pool")(x)
        elif pooling == "max":
            x = layers.GlobalMaxPooling2D(name="max_pool")(x)
    # Ensure that the model takes into account
    # any potential predecessors of `input_tensor`.
    if input_tensor is not None:
        inputs = operation_utils.get_source_inputs(input_tensor)
    else:
        inputs = img_input

    # Create model.
    model = Functional(inputs, x, name=name)

    # Load weights.
    if weights == "imagenet":
        model_name = "{}{}_224_{}_float".format(
            model_type, "_minimalistic" if minimalistic else "", str(alpha)
        )
        if include_top:
            file_name = f"weights_mobilenet_v3_{model_name}.h5"
            file_hash = WEIGHTS_HASHES[model_name][0]
        else:
            file_name = f"weights_mobilenet_v3_{model_name}_no_top_v2.h5"
            file_hash = WEIGHTS_HASHES[model_name][1]
        weights_path = file_utils.get_file(
            file_name,
            BASE_WEIGHT_PATH + file_name,
            cache_subdir="models",
            file_hash=file_hash,
        )
        model.load_weights(weights_path)
    elif weights is not None:
        model.load_weights(weights)

    return model