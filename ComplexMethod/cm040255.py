def ResNet(
    stack_fn,
    preact,
    use_bias,
    include_top=True,
    weights="imagenet",
    input_tensor=None,
    input_shape=None,
    pooling=None,
    classes=1000,
    classifier_activation="softmax",
    name="resnet",
    weights_name=None,
):
    """Instantiates the ResNet, ResNetV2, and ResNeXt architecture.

    Args:
        stack_fn: A function that returns output tensor for the
            stacked residual blocks.
        preact: Whether to use pre-activation or not. `True` for ResNetV2,
            `False` for ResNet and ResNeXt.
        use_bias: Whether to use biases for convolutional layers or not.
            `True` for ResNet and ResNetV2, `False` for ResNeXt.
        name: Name of the model.
        include_top: Whether to include the fully-connected
            layer at the top of the network.
        weights: One of `None` (random initialization),
            `"imagenet"` (pre-training on ImageNet),
            or the path to the weights file to be loaded.
        input_tensor: Optional Keras tensor (i.e. output of `layers.Input()`)
            to use as image input for the model.
        input_shape: Optional shape tuple, only to be specified
            if `include_top` is `False` (otherwise the input shape
            has to be `(224, 224, 3)` (with `channels_last` data format)
            or `(3, 224, 224)` (with `"channels_first"` data format). It
            should have exactly 3 inputs channels.
        pooling: Optional pooling mode for feature extraction
            when `include_top` is `False`.
            - `None` means that the output of the model will be
                the 4D tensor output of the
                last convolutional layer.
            - `avg` means that global average pooling
                will be applied to the output of the
                last convolutional layer, and thus
                the output of the model will be a 2D tensor.
            - `max` means that global max pooling will
                be applied.
        classes: optional number of classes to classify images
            into, only to be specified if `include_top` is `True`,
            and if no `weights` argument is specified.
        classifier_activation: A `str` or callable. The activation
            function to use on the "top" layer. Ignored unless
            `include_top=True`. Set `classifier_activation=None` to
            return the logits of the "top" layer. When loading
            pretrained weights, `classifier_activation` can only be
            `None` or `"softmax"`.
        name: The name of the model (string).

    Returns:
        A Model instance.
    """

    if not (weights in {"imagenet", None} or file_utils.exists(weights)):
        raise ValueError(
            "The `weights` argument should be either "
            "`None` (random initialization), 'imagenet' "
            "(pre-training on ImageNet), "
            "or the path to the weights file to be loaded.  Received: "
            f"weights={weights}"
        )

    if weights == "imagenet" and include_top and classes != 1000:
        raise ValueError(
            "If using `weights='imagenet'` with `include_top=True`, "
            "`classes` should be 1000.  "
            f"Received classes={classes}"
        )

    # Determine proper input shape
    input_shape = imagenet_utils.obtain_input_shape(
        input_shape,
        default_size=224,
        min_size=32,
        data_format=backend.image_data_format(),
        require_flatten=include_top,
        weights=weights,
    )

    if input_tensor is None:
        img_input = layers.Input(shape=input_shape)
    else:
        if not backend.is_keras_tensor(input_tensor):
            img_input = layers.Input(tensor=input_tensor, shape=input_shape)
        else:
            img_input = input_tensor

    if backend.image_data_format() == "channels_last":
        bn_axis = 3
    else:
        bn_axis = 1

    x = layers.ZeroPadding2D(padding=((3, 3), (3, 3)), name="conv1_pad")(
        img_input
    )
    x = layers.Conv2D(64, 7, strides=2, use_bias=use_bias, name="conv1_conv")(x)

    if not preact:
        x = layers.BatchNormalization(
            axis=bn_axis, epsilon=1.001e-5, name="conv1_bn"
        )(x)
        x = layers.Activation("relu", name="conv1_relu")(x)

    x = layers.ZeroPadding2D(padding=((1, 1), (1, 1)), name="pool1_pad")(x)
    x = layers.MaxPooling2D(3, strides=2, name="pool1_pool")(x)

    x = stack_fn(x)

    if preact:
        x = layers.BatchNormalization(
            axis=bn_axis, epsilon=1.001e-5, name="post_bn"
        )(x)
        x = layers.Activation("relu", name="post_relu")(x)

    if include_top:
        x = layers.GlobalAveragePooling2D(name="avg_pool")(x)

        # Validate activation for the classifier layer
        imagenet_utils.validate_activation(classifier_activation, weights)

        x = layers.Dense(
            classes, activation=classifier_activation, name="predictions"
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
    if (weights == "imagenet") and (weights_name in WEIGHTS_HASHES):
        if include_top:
            file_name = f"{weights_name}_weights_tf_dim_ordering_tf_kernels.h5"
            file_hash = WEIGHTS_HASHES[weights_name][0]
        else:
            file_name = (
                f"{weights_name}_weights_tf_dim_ordering_tf_kernels_notop.h5"
            )
            file_hash = WEIGHTS_HASHES[weights_name][1]
        weights_path = file_utils.get_file(
            file_name,
            f"{BASE_WEIGHTS_PATH}{file_name}",
            cache_subdir="models",
            file_hash=file_hash,
        )
        model.load_weights(weights_path)
    elif weights is not None:
        model.load_weights(weights)

    return model