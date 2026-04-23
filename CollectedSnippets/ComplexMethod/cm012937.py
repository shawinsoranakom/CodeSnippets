def get_base_name_to_sets_of_related_ops() -> dict[str, set[NSNodeTargetType]]:
    # note: this set is modified below by items from backend_config
    sets_of_related_ops: list[set[NSNodeTargetType]] = [
        # conv modules
        {
            nn.Conv1d,
        },
        {
            nn.Conv2d,
        },
        {
            nn.Conv3d,
        },
        # conv functionals
        {
            F.conv1d,
        },
        {
            F.conv2d,
        },
        {
            F.conv3d,
        },
        # linear modules
        {
            nn.Linear,
        },
        # linear functionals
        {
            F.linear,
        },
        # average pool
        {
            nn.AvgPool1d,
            torch.avg_pool1d,
        },
        {
            nn.AvgPool2d,
            torch._C._nn.avg_pool2d,
        },
        {
            nn.AvgPool3d,
            torch._C._nn.avg_pool3d,
        },
        # adaptive average pool
        {
            nn.AdaptiveAvgPool1d,
            F.adaptive_avg_pool1d,
        },
        {
            nn.AdaptiveAvgPool2d,
            F.adaptive_avg_pool2d,
        },
        {
            nn.AdaptiveAvgPool3d,
            F.adaptive_avg_pool3d,
        },
        # LSTM
        {
            nn.LSTM,
        },
        # add
        {
            torch.add,
            operator.add,  # x + y
        },
        # cat
        {
            torch.cat,
        },
        # mul
        {
            torch.mul,
            operator.mul,
        },
        # relu
        {
            F.relu,
            nn.ReLU,
            "relu",
            "relu_",
            torch.relu,
        },
        # maxpool
        {
            nn.MaxPool1d,
            F.max_pool1d,
        },
        {
            nn.MaxPool2d,
            F.max_pool2d,
        },
        {
            nn.MaxPool3d,
            F.max_pool3d,
        },
        # sigmoid
        {
            torch.sigmoid,
            "sigmoid",
            "sigmoid_",
            nn.Sigmoid,
            F.sigmoid,
        },
        # BatchNorm
        {
            nn.BatchNorm2d,
        },
        {
            nn.BatchNorm3d,
        },
        # ConvTranspose
        {
            nn.ConvTranspose1d,
        },
        {
            nn.ConvTranspose2d,
        },
        {
            nn.ConvTranspose3d,
        },
        # functional transposed conv
        {
            F.conv_transpose1d,
        },
        {
            F.conv_transpose2d,
        },
        {
            F.conv_transpose3d,
        },
        # ELU
        {
            nn.ELU,
        },
        # Embedding
        {
            nn.Embedding,
        },
        # EmbeddingBag
        {
            nn.EmbeddingBag,
        },
        # GroupNorm
        {
            nn.GroupNorm,
        },
        # Hardswish
        {
            nn.Hardswish,
        },
        # InstanceNorm
        {
            nn.InstanceNorm1d,
        },
        {
            nn.InstanceNorm2d,
        },
        {
            nn.InstanceNorm3d,
        },
        # LayerNorm
        {
            nn.LayerNorm,
        },
        # LeakyReLU
        {
            nn.LeakyReLU,
        },
        # ReLU6
        {
            nn.ReLU6,
            F.relu6,
        },
        # F.elu
        {
            F.elu,
        },
        # F.hardswish
        {
            F.hardswish,
        },
        # F.group_norm
        {
            F.group_norm,
        },
        # F.instance_norm
        {
            F.instance_norm,
        },
        # F.layer_norm
        {
            F.layer_norm,
        },
        # F.leaky_relu
        {
            F.leaky_relu,
        },
        # F.silu
        {
            nn.SiLU,
            F.silu,
        },
        # F.mish
        {
            nn.Mish,
            F.mish,
        },
        # F.tanh
        {
            nn.Tanh,
            F.tanh,
            torch.tanh,
            "tanh_",
            "tanh",
        },
        # F.hardsigmoid
        {
            "hardsigmoid_",
            "hardsigmoid",
            F.hardsigmoid,
            nn.Hardsigmoid,
        },
        # F.hardtanh
        {
            nn.Hardtanh,
            F.hardtanh,
            F.hardtanh_,
        },
        # floordiv
        {
            operator.floordiv,
        },
        # unsqueeze
        {
            torch.unsqueeze,
        },
        # stack
        {
            torch.stack,
        },
        # squeeze
        {
            torch.squeeze,
        },
        # sort
        {
            torch.sort,
        },
        # repeat_interleave
        {
            torch.repeat_interleave,
        },
        # min
        {
            torch.min,
        },
        # mean
        {
            torch.mean,
        },
        # max
        {
            torch.max,
        },
        # transpose
        {
            torch.transpose,
        },
        # flatten
        {
            torch.flatten,
        },
        # clamp
        {
            torch.clamp,
        },
        # chunk
        {
            torch.chunk,
        },
        # interpolate
        {
            torch.nn.functional.interpolate,
        },
        # dropout
        {
            nn.Dropout,
        },
        # F.dropout
        {
            F.dropout,
        },
        # matmul
        {
            torch.matmul,
        },
        # Softmax
        {
            nn.Softmax,
        },
        # PReLU
        {
            nn.PReLU,
            nnq.PReLU,
        },
        # F.prelu
        {
            F.prelu,
            toq.prelu,
        },
        # pixel shuffle
        {
            nn.PixelShuffle,
        },
        {
            F.pixel_shuffle,
        },
        # pixel unshuffle
        {
            nn.PixelUnshuffle,
        },
        {
            F.pixel_unshuffle,
        },
        # narrow
        {
            torch.narrow,
        },
    ]

    # for each floating point op, add versions of the op added by
    # backend_config
    backend_config = get_native_backend_config()

    new_connections: list[tuple[Callable, Callable]] = [
        # technical debt edge case
        (nn.Linear, nn.modules.linear.NonDynamicallyQuantizableLinear),
    ]

    for pattern, config in backend_config._pattern_complex_format_to_config.items():
        # pattern format: (c, (b, a))
        first_element = pattern
        # look from the end, because pattern is in reverse order
        while isinstance(first_element, (list, tuple)):
            first_element = first_element[-1]

        if config.fused_module is not None:
            # case 1: pattern fuses a pattern of ops into an op
            # example: nn.Conv1d, nn.ReLU fused into nni.ConvReLU1d
            new_connections.append((first_element, config.fused_module))

        if config.qat_module is not None:
            # case 2: pattern swaps a module into a QAT module
            # example: nni.ConvReLU1d swapped into nniqat.ConvReLU1d
            new_connections.append((first_element, config.qat_module))

        if config.reference_quantized_module is not None:
            # case 3: reference version of floating point module, such as
            # nn.Conv2d and nnqr.Conv2d
            new_connections.append((first_element, config.reference_quantized_module))

    #
    # Add reference module swaps from default lowering path
    #

    for source_to_target in (
        _lower_to_native_backend.STATIC_LOWER_MODULE_MAP,
        _lower_to_native_backend.DYNAMIC_LOWER_MODULE_MAP,
        _lower_to_native_backend.WEIGHT_ONLY_LOWER_MODULE_MAP,
        _lower_to_native_backend.SPECIAL_PATTERN_LOWER_MODULE_MAP,
    ):
        for source, target in source_to_target.items():  # type: ignore[attr-defined]
            new_connections.append((source, target))

    for source_to_double_target in (
        _lower_to_native_backend.STATIC_LOWER_FUSED_MODULE_MAP,
        _lower_to_native_backend.STATIC_LOWER_FUSED_MODULE_TWO_INPUTS_MAP,
        _lower_to_native_backend.DYNAMIC_LOWER_FUSED_MODULE_MAP,
    ):
        for source, (target1, target2) in source_to_double_target.items():  # type: ignore[attr-defined]
            new_connections.append((source, target1))
            new_connections.append((source, target2))

    #
    # Add function swaps from default lowering path
    #

    for source, (  # type:ignore[assignment]
        target1,
        target2,
    ) in _lower_to_native_backend.STATIC_LOWER_FUNCTIONAL_MAP.items():
        new_connections.append((source, target1))
        # pyrefly: ignore [bad-argument-type]
        new_connections.append((source, target2))

    for source_to_target in (
        _lower_to_native_backend.QBIN_OP_MAPPING,
        _lower_to_native_backend.QBIN_RELU_OP_MAPPING,
        quantization_mappings.DEFAULT_FLOAT_TO_QUANTIZED_OPERATOR_MAPPINGS,
    ):
        for source, target in source_to_target.items():  # type:ignore[assignment]
            # pyrefly: ignore [bad-argument-type]
            new_connections.append((source, target))

    #
    # Add other swaps, ideally in the future this could be removed
    # after the lowering code stops using these.
    #
    for source_to_target in (
        quantization_mappings.DEFAULT_DYNAMIC_QUANT_MODULE_MAPPINGS,
    ):
        for source, target in source_to_target.items():  # type:ignore[assignment]
            new_connections.append((source, target))

    # add the new connections from backend_config
    for item1, item2 in new_connections:
        for set_of_related_ops in sets_of_related_ops:
            if item1 in set_of_related_ops or item2 in set_of_related_ops:
                set_of_related_ops.add(item1)
                set_of_related_ops.add(item2)
                break

    base_name_to_sets_of_related_ops: dict[str, set[NSNodeTargetType]] = {}

    for counter, set_of_related_ops in enumerate(sets_of_related_ops):
        base_name = str(counter)
        base_name_to_sets_of_related_ops[base_name] = set_of_related_ops

    return base_name_to_sets_of_related_ops