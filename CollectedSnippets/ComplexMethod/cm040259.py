def NASNet(
    input_shape=None,
    penultimate_filters=4032,
    num_blocks=6,
    stem_block_filters=96,
    skip_reduction=True,
    filter_multiplier=2,
    include_top=True,
    weights="imagenet",
    input_tensor=None,
    pooling=None,
    classes=1000,
    default_size=None,
    classifier_activation="softmax",
    name="NASNet",
):
    """Instantiates a NASNet model.

    Reference:
    - [Learning Transferable Architectures for Scalable Image Recognition](
        https://arxiv.org/abs/1707.07012) (CVPR 2018)

    For image classification use cases, see
    [this page for detailed examples](
      https://keras.io/api/applications/#usage-examples-for-image-classification-models).

    For transfer learning use cases, make sure to read the
    [guide to transfer learning & fine-tuning](
      https://keras.io/guides/transfer_learning/).

    Note: each Keras Application expects a specific kind of input preprocessing.
    For NasNet, call `keras.applications.nasnet.preprocess_input`
    on your inputs before passing them to the model.
    `nasnet.preprocess_input` will scale input pixels between -1 and 1.

    Args:
        input_shape: Optional shape tuple, the input shape
            is by default `(331, 331, 3)` for NASNetLarge and
            `(224, 224, 3)` for NASNetMobile.
            It should have exactly 3 input channels,
            and width and height should be no smaller than 32.
            E.g. `(224, 224, 3)` would be one valid value.
        penultimate_filters: Number of filters in the penultimate layer.
            NASNet models use the notation `NASNet (N @ P)`, where:
                -   N is the number of blocks
                -   P is the number of penultimate filters
        num_blocks: Number of repeated blocks of the NASNet model.
            NASNet models use the notation `NASNet (N @ P)`, where:
                -   N is the number of blocks
                -   P is the number of penultimate filters
        stem_block_filters: Number of filters in the initial stem block
        skip_reduction: Whether to skip the reduction step at the tail
            end of the network.
        filter_multiplier: Controls the width of the network.
            - If `filter_multiplier` < 1.0, proportionally decreases the number
                of filters in each layer.
            - If `filter_multiplier` > 1.0, proportionally increases the number
                of filters in each layer.
            - If `filter_multiplier` = 1, default number of filters from the
                paper are used at each layer.
        include_top: Whether to include the fully-connected
            layer at the top of the network.
        weights: `None` (random initialization) or
            `imagenet` (ImageNet weights)
        input_tensor: Optional Keras tensor (i.e. output of
            `layers.Input()`)
            to use as image input for the model.
        pooling: Optional pooling mode for feature extraction
            when `include_top` is `False`.
            - `None` means that the output of the model
                will be the 4D tensor output of the
                last convolutional block.
            - `avg` means that global average pooling
                will be applied to the output of the
                last convolutional block, and thus
                the output of the model will be a
                2D tensor.
            - `max` means that global max pooling will
                be applied.
        classes: Optional number of classes to classify images
            into, only to be specified if `include_top` is `True`, and
            if no `weights` argument is specified.
        default_size: Specifies the default image size of the model
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
    if backend.image_data_format() == "channels_first":
        raise ValueError(
            "NASNet does not support the `channels_first` image data "
            "format. Switch to `channels_last` by editing your local "
            "config file at ~/.keras/keras.json"
        )
    if not (weights in {"imagenet", None} or file_utils.exists(weights)):
        raise ValueError(
            "The `weights` argument should be either "
            "`None` (random initialization), `imagenet` "
            "(pre-training on ImageNet), "
            "or the path to the weights file to be loaded."
        )

    if weights == "imagenet" and include_top and classes != 1000:
        raise ValueError(
            'If using `weights` as `"imagenet"` with `include_top` '
            "as true, `classes` should be 1000"
        )

    if (
        isinstance(input_shape, tuple)
        and None in input_shape
        and weights == "imagenet"
    ):
        raise ValueError(
            "When specifying the input shape of a NASNet and loading "
            "`ImageNet` weights, the input_shape argument must be static"
            f" (no None entries). Got: `input_shape={input_shape}`."
        )

    if default_size is None:
        default_size = 331

    # Determine proper input shape and default size.
    input_shape = imagenet_utils.obtain_input_shape(
        input_shape,
        default_size=default_size,
        min_size=32,
        data_format=backend.image_data_format(),
        require_flatten=include_top,
        weights=weights,
    )

    if backend.image_data_format() != "channels_last":
        warnings.warn(
            "The NASNet family of models is only available "
            'for the input data format "channels_last" '
            "(width, height, channels). "
            "However your settings specify the default "
            'data format "channels_first" (channels, width, height).'
            ' You should set `image_data_format="channels_last"` '
            "in your Keras config located at ~/.keras/keras.json. "
            "The model being returned right now will expect inputs "
            'to follow the "channels_last" data format.',
            stacklevel=2,
        )

    if input_tensor is None:
        img_input = layers.Input(shape=input_shape)
    else:
        if not backend.is_keras_tensor(input_tensor):
            img_input = layers.Input(tensor=input_tensor, shape=input_shape)
        else:
            img_input = input_tensor

    if penultimate_filters % (24 * (filter_multiplier**2)) != 0:
        raise ValueError(
            "For NASNet-A models, the `penultimate_filters` must be a multiple "
            "of 24 * (`filter_multiplier` ** 2). "
            f"Current value: {penultimate_filters}"
        )

    channel_dim = 1 if backend.image_data_format() == "channels_first" else -1
    filters = penultimate_filters // 24

    x = layers.Conv2D(
        stem_block_filters,
        (3, 3),
        strides=(2, 2),
        padding="valid",
        use_bias=False,
        name="stem_conv1",
        kernel_initializer="he_normal",
    )(img_input)

    x = layers.BatchNormalization(
        axis=channel_dim, momentum=0.9997, epsilon=1e-3, name="stem_bn1"
    )(x)

    p = None
    x, p = _reduction_a_cell(
        x, p, filters // (filter_multiplier**2), block_id="stem_1"
    )
    x, p = _reduction_a_cell(
        x, p, filters // filter_multiplier, block_id="stem_2"
    )

    for i in range(num_blocks):
        x, p = _normal_a_cell(x, p, filters, block_id=f"{i}")

    x, p0 = _reduction_a_cell(
        x, p, filters * filter_multiplier, block_id=f"reduce_{num_blocks}"
    )

    p = p0 if not skip_reduction else p

    for i in range(num_blocks):
        x, p = _normal_a_cell(
            x,
            p,
            filters * filter_multiplier,
            block_id=f"{num_blocks + i + 1}",
        )

    x, p0 = _reduction_a_cell(
        x,
        p,
        filters * filter_multiplier**2,
        block_id=f"reduce_{2 * num_blocks}",
    )

    p = p0 if not skip_reduction else p

    for i in range(num_blocks):
        x, p = _normal_a_cell(
            x,
            p,
            filters * filter_multiplier**2,
            block_id=f"{2 * num_blocks + i + 1}",
        )

    x = layers.Activation("relu")(x)

    if include_top:
        x = layers.GlobalAveragePooling2D()(x)
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

    model = Functional(inputs, x, name=name)

    # Load weights.
    if weights == "imagenet":
        if default_size == 224:  # mobile version
            if include_top:
                weights_path = file_utils.get_file(
                    "nasnet_mobile.h5",
                    NASNET_MOBILE_WEIGHT_PATH,
                    cache_subdir="models",
                    file_hash="020fb642bf7360b370c678b08e0adf61",
                )
            else:
                weights_path = file_utils.get_file(
                    "nasnet_mobile_no_top.h5",
                    NASNET_MOBILE_WEIGHT_PATH_NO_TOP,
                    cache_subdir="models",
                    file_hash="1ed92395b5b598bdda52abe5c0dbfd63",
                )
            model.load_weights(weights_path)
        elif default_size == 331:  # large version
            if include_top:
                weights_path = file_utils.get_file(
                    "nasnet_large.h5",
                    NASNET_LARGE_WEIGHT_PATH,
                    cache_subdir="models",
                    file_hash="11577c9a518f0070763c2b964a382f17",
                )
            else:
                weights_path = file_utils.get_file(
                    "nasnet_large_no_top.h5",
                    NASNET_LARGE_WEIGHT_PATH_NO_TOP,
                    cache_subdir="models",
                    file_hash="d81d89dc07e6e56530c4e77faddd61b5",
                )
            model.load_weights(weights_path)
        else:
            raise ValueError(
                "ImageNet weights can only be loaded with NASNetLarge"
                " or NASNetMobile"
            )
    elif weights is not None:
        model.load_weights(weights)

    return model