def InceptionResNetV2(
    include_top=True,
    weights="imagenet",
    input_tensor=None,
    input_shape=None,
    pooling=None,
    classes=1000,
    classifier_activation="softmax",
    name="inception_resnet_v2",
):
    """Instantiates the Inception-ResNet v2 architecture.

    Reference:
    - [Inception-v4, Inception-ResNet and the Impact of
       Residual Connections on Learning](https://arxiv.org/abs/1602.07261)
      (AAAI 2017)

    This function returns a Keras image classification model,
    optionally loaded with weights pre-trained on ImageNet.

    For image classification use cases, see
    [this page for detailed examples](
      https://keras.io/api/applications/#usage-examples-for-image-classification-models).

    For transfer learning use cases, make sure to read the
    [guide to transfer learning & fine-tuning](
      https://keras.io/guides/transfer_learning/).

    Note: each Keras Application expects a specific kind of
    input preprocessing. For InceptionResNetV2, call
    `keras.applications.inception_resnet_v2.preprocess_input`
    on your inputs before passing them to the model.
    `inception_resnet_v2.preprocess_input`
    will scale input pixels between -1 and 1.

    Args:
        include_top: whether to include the fully-connected
            layer at the top of the network.
        weights: one of `None` (random initialization),
            `"imagenet"` (pre-training on ImageNet),
            or the path to the weights file to be loaded.
        input_tensor: optional Keras tensor
            (i.e. output of `layers.Input()`)
            to use as image input for the model.
        input_shape: optional shape tuple, only to be specified
            if `include_top` is `False` (otherwise the input shape
            has to be `(299, 299, 3)`
            (with `'channels_last'` data format)
            or `(3, 299, 299)` (with `'channels_first'` data format).
            It should have exactly 3 inputs channels,
            and width and height should be no smaller than 75.
            E.g. `(150, 150, 3)` would be one valid value.
        pooling: Optional pooling mode for feature extraction
            when `include_top` is `False`.
            - `None` means that the output of the model will be
                the 4D tensor output of the last convolutional block.
            - `'avg'` means that global average pooling
                will be applied to the output of the
                last convolutional block, and thus
                the output of the model will be a 2D tensor.
            - `'max'` means that global max pooling will be applied.
        classes: optional number of classes to classify images
            into, only to be specified if `include_top` is `True`,
            and if no `weights` argument is specified.
        classifier_activation: A `str` or callable.
            The activation function to use on the "top" layer.
            Ignored unless `include_top=True`.
            Set `classifier_activation=None` to return the logits
            of the "top" layer. When loading pretrained weights,
            `classifier_activation` can only be `None` or `"softmax"`.
        name: The name of the model (string).

    Returns:
        A model instance.
    """
    if not (weights in {"imagenet", None} or file_utils.exists(weights)):
        raise ValueError(
            "The `weights` argument should be either "
            "`None` (random initialization), `imagenet` "
            "(pre-training on ImageNet), "
            "or the path to the weights file to be loaded."
        )

    if weights == "imagenet" and include_top and classes != 1000:
        raise ValueError(
            'If using `weights="imagenet"` with `include_top=True`, '
            "`classes` should be 1000. "
            f"Received classes={classes}"
        )

    # Determine proper input shape
    input_shape = imagenet_utils.obtain_input_shape(
        input_shape,
        default_size=299,
        min_size=75,
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

    # Stem block: 35 x 35 x 192
    x = conv2d_bn(img_input, 32, 3, strides=2, padding="valid")
    x = conv2d_bn(x, 32, 3, padding="valid")
    x = conv2d_bn(x, 64, 3)
    x = layers.MaxPooling2D(3, strides=2)(x)
    x = conv2d_bn(x, 80, 1, padding="valid")
    x = conv2d_bn(x, 192, 3, padding="valid")
    x = layers.MaxPooling2D(3, strides=2)(x)

    # Mixed 5b (Inception-A block): 35 x 35 x 320
    branch_0 = conv2d_bn(x, 96, 1)
    branch_1 = conv2d_bn(x, 48, 1)
    branch_1 = conv2d_bn(branch_1, 64, 5)
    branch_2 = conv2d_bn(x, 64, 1)
    branch_2 = conv2d_bn(branch_2, 96, 3)
    branch_2 = conv2d_bn(branch_2, 96, 3)
    branch_pool = layers.AveragePooling2D(3, strides=1, padding="same")(x)
    branch_pool = conv2d_bn(branch_pool, 64, 1)
    branches = [branch_0, branch_1, branch_2, branch_pool]
    channel_axis = 1 if backend.image_data_format() == "channels_first" else 3
    x = layers.Concatenate(axis=channel_axis, name="mixed_5b")(branches)

    # 10x block35 (Inception-ResNet-A block): 35 x 35 x 320
    for block_idx in range(1, 11):
        x = inception_resnet_block(
            x, scale=0.17, block_type="block35", block_idx=block_idx
        )

    # Mixed 6a (Reduction-A block): 17 x 17 x 1088
    branch_0 = conv2d_bn(x, 384, 3, strides=2, padding="valid")
    branch_1 = conv2d_bn(x, 256, 1)
    branch_1 = conv2d_bn(branch_1, 256, 3)
    branch_1 = conv2d_bn(branch_1, 384, 3, strides=2, padding="valid")
    branch_pool = layers.MaxPooling2D(3, strides=2, padding="valid")(x)
    branches = [branch_0, branch_1, branch_pool]
    x = layers.Concatenate(axis=channel_axis, name="mixed_6a")(branches)

    # 20x block17 (Inception-ResNet-B block): 17 x 17 x 1088
    for block_idx in range(1, 21):
        x = inception_resnet_block(
            x, scale=0.1, block_type="block17", block_idx=block_idx
        )

    # Mixed 7a (Reduction-B block): 8 x 8 x 2080
    branch_0 = conv2d_bn(x, 256, 1)
    branch_0 = conv2d_bn(branch_0, 384, 3, strides=2, padding="valid")
    branch_1 = conv2d_bn(x, 256, 1)
    branch_1 = conv2d_bn(branch_1, 288, 3, strides=2, padding="valid")
    branch_2 = conv2d_bn(x, 256, 1)
    branch_2 = conv2d_bn(branch_2, 288, 3)
    branch_2 = conv2d_bn(branch_2, 320, 3, strides=2, padding="valid")
    branch_pool = layers.MaxPooling2D(3, strides=2, padding="valid")(x)
    branches = [branch_0, branch_1, branch_2, branch_pool]
    x = layers.Concatenate(axis=channel_axis, name="mixed_7a")(branches)

    # 10x block8 (Inception-ResNet-C block): 8 x 8 x 2080
    for block_idx in range(1, 10):
        x = inception_resnet_block(
            x, scale=0.2, block_type="block8", block_idx=block_idx
        )
    x = inception_resnet_block(
        x, scale=1.0, activation=None, block_type="block8", block_idx=10
    )

    # Final convolution block: 8 x 8 x 1536
    x = conv2d_bn(x, 1536, 1, name="conv_7b")

    if include_top:
        # Classification block
        x = layers.GlobalAveragePooling2D(name="avg_pool")(x)
        imagenet_utils.validate_activation(classifier_activation, weights)
        x = layers.Dense(
            classes, activation=classifier_activation, name="predictions"
        )(x)
    else:
        if pooling == "avg":
            x = layers.GlobalAveragePooling2D()(x)
        elif pooling == "max":
            x = layers.GlobalMaxPooling2D()(x)

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
        if include_top:
            fname = "inception_resnet_v2_weights_tf_dim_ordering_tf_kernels.h5"
            weights_path = file_utils.get_file(
                fname,
                BASE_WEIGHT_URL + fname,
                cache_subdir="models",
                file_hash="e693bd0210a403b3192acc6073ad2e96",
            )
        else:
            fname = (
                "inception_resnet_v2_weights_"
                "tf_dim_ordering_tf_kernels_notop.h5"
            )
            weights_path = file_utils.get_file(
                fname,
                BASE_WEIGHT_URL + fname,
                cache_subdir="models",
                file_hash="d19885ff4a710c122648d3b5c3b684e4",
            )
        model.load_weights(weights_path)
    elif weights is not None:
        model.load_weights(weights)

    return model