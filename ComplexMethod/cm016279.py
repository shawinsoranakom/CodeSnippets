def gen_nn_functional(fm: FileManager) -> None:
    INPUT = "input: Tensor"
    KERNEL_SIZE = "kernel_size: _int | _size"
    STRIDE_PADDING = [
        "stride: _int | _size | None = None",
        "padding: _int | _size = 0",
    ]

    # TODO the list for `torch._C._nn` is nonexhaustive
    unsorted_c_nn_function_hints: dict[str, list[str]] = {}

    for d in (2, 3):
        unsorted_c_nn_function_hints.update(
            {
                f"avg_pool{d}d": [
                    defs(
                        f"avg_pool{d}d",
                        [
                            INPUT,
                            KERNEL_SIZE,
                            *STRIDE_PADDING,
                            "ceil_mode: bool = False",
                            "count_include_pad: bool = True",
                            "divisor_override: int | None = None",
                        ],
                        "Tensor",
                    )
                ],
                f"fractional_max_pool{d}d": [
                    defs(
                        f"fractional_max_pool{d}d",
                        [
                            INPUT,
                            KERNEL_SIZE,
                            "output_size: _int | _size",
                            "_random_samples: Tensor",
                        ],
                        "tuple[Tensor, Tensor]",
                    )
                ],
                f"adaptive_max_pool{d}d": [
                    defs(
                        f"adaptive_max_pool{d}d",
                        [
                            INPUT,
                            "output_size: _int | _size",
                        ],
                        "tuple[Tensor, Tensor]",
                    )
                ],
                f"adaptive_avg_pool{d}d": [
                    defs(
                        f"adaptive_avg_pool{d}d",
                        [
                            INPUT,
                            "output_size: _int | _size",
                        ],
                        "Tensor",
                    )
                ],
                f"max_pool{d}d_with_indices": [
                    defs(
                        f"max_pool{d}d_with_indices",
                        [
                            INPUT,
                            KERNEL_SIZE,
                            *STRIDE_PADDING,
                            "dilation: _int | _size = 1",
                            "ceil_mode: bool = False",
                        ],
                        "tuple[Tensor, Tensor]",
                    )
                ],
            }
        )

    unsorted_c_nn_function_hints.update(
        {
            "hardtanh": [
                defs(
                    "hardtanh",
                    [
                        "input: Tensor",
                        "min_val: float = ...",
                        "max_val: float = ...",
                        "*",
                        "out: Tensor | None = None",
                    ],
                    "Tensor",
                )
            ],
            "hardtanh_": [
                defs(
                    "hardtanh_",
                    ["input: Tensor", "min_val: float = ...", "max_val: float = ..."],
                    "Tensor",
                ),
            ],
            "elu_": [defs("elu_", ["input: Tensor", "alpha: float = ..."], "Tensor")],
            "leaky_relu": [
                defs(
                    "leaky_relu",
                    [
                        "input: Tensor",
                        "negative_slope: float = ...",
                        "*",
                        "out: Tensor | None = None",
                    ],
                    "Tensor",
                )
            ],
            "leaky_relu_": [
                defs(
                    "leaky_relu_",
                    ["input: Tensor", "negative_slope: float = ..."],
                    "Tensor",
                )
            ],
            "log_sigmoid": [defs("log_sigmoid", ["input: Tensor"], "Tensor")],
            "gelu": [
                defs("gelu", ["input: Tensor", "approximate: str = ..."], "Tensor")
            ],
            "softplus": [
                defs(
                    "softplus",
                    ["input: Tensor", "beta: float = ...", "threshold: float = ..."],
                    "Tensor",
                )
            ],
            "softshrink": [
                defs("softshrink", ["input: Tensor", "lambd: float = ..."], "Tensor")
            ],
            "hardsigmoid": [
                defs(
                    "hardsigmoid",
                    ["input: Tensor", "*", "out: Tensor | None = None"],
                    "Tensor",
                )
            ],
            "linear": [
                defs(
                    "linear",
                    ["input: Tensor", "weight: Tensor", "bias: Tensor | None = None"],
                    "Tensor",
                )
            ],
            "pad": [
                defs(
                    "pad",
                    [
                        "input: Tensor",
                        "pad: Sequence[int]",
                        "mode: str = ...",
                        "value: float | None = None",
                    ],
                    "Tensor",
                )
            ],
            "one_hot": [
                defs("one_hot", ["tensor: Tensor", "num_classes: int = ..."], "Tensor")
            ],
            "scaled_dot_product_attention": [
                defs(
                    "scaled_dot_product_attention",
                    [
                        "query: Tensor",
                        "key: Tensor",
                        "value: Tensor",
                        "attn_mask: Tensor | None = None",
                        "dropout_p: float = 0.0",
                        "is_causal: bool = False",
                        "scale: float | None = None",
                        "enable_gqa: bool = False",
                    ],
                    "Tensor",
                )
            ],
            "binary_cross_entropy": [
                defs(
                    "binary_cross_entropy",
                    [
                        INPUT,
                        "target: Tensor",
                        "weight: Tensor | None = None",
                        "reduction: str = ...",
                    ],
                    "Tensor",
                )
            ],
            "col2im": [
                defs(
                    "col2im",
                    [
                        INPUT,
                        "output_size: _int | _size",
                        KERNEL_SIZE,
                        "dilation: _int | _size",
                        *STRIDE_PADDING,
                    ],
                    "Tensor",
                )
            ],
            "elu": [
                defs(
                    "elu",
                    [
                        INPUT,
                        "alpha: float = 1.0",
                        "scale: float = 1.0",
                        "input_scale: float = 1.0",
                    ],
                    "Tensor",
                )
            ],
            "glu": [
                defs(
                    "glu",
                    [
                        INPUT,
                        "dim: int = -1",
                    ],
                    "Tensor",
                )
            ],
            "max_unpool2d": [
                defs(
                    "max_unpool2d",
                    [
                        INPUT,
                        "indices: Tensor",
                        "output_size: Sequence[int] | None",
                    ],
                    "Tensor",
                )
            ],
            "max_unpool3d": [
                defs(
                    "max_unpool3d",
                    [
                        INPUT,
                        "indices: Tensor",
                        "output_size: Sequence[int] | None",
                        "stride: _int | _size",
                        "padding: _int | _size",
                    ],
                    "Tensor",
                )
            ],
            "cross_entropy_loss": [
                defs(
                    "cross_entropy_loss",
                    [
                        INPUT,
                        "target: Tensor",
                        "weight: Tensor | None = None",
                        "reduction: str = ...",
                        "ignore_index: int = -100",
                        "label_smoothing: float = 0.0",
                    ],
                    "Tensor",
                )
            ],
            "hardsigmoid_": [
                defs(
                    "hardsigmoid_",
                    [
                        INPUT,
                    ],
                    "Tensor",
                )
            ],
            "hardswish": [
                defs(
                    "hardswish",
                    [
                        INPUT,
                    ],
                    "Tensor",
                )
            ],
            "hardswish_": [
                defs(
                    "hardswish_",
                    [
                        INPUT,
                    ],
                    "Tensor",
                )
            ],
            "huber_loss": [
                defs(
                    "huber_loss",
                    [
                        INPUT,
                        "target: Tensor",
                        "reduction: str = ...",
                        "delta: float = 1.0",
                    ],
                    "Tensor",
                )
            ],
            "im2col": [
                defs(
                    "im2col",
                    [
                        INPUT,
                        KERNEL_SIZE,
                        "dilation: _int | _size",
                        "padding: _int | _size",
                        "stride: _int | _size",
                    ],
                    "Tensor",
                )
            ],
            "l1_loss": [
                defs(
                    "l1_loss",
                    [
                        INPUT,
                        "target: Tensor",
                        "reduction: str = ...",
                    ],
                    "Tensor",
                )
            ],
            "mish": [
                defs(
                    "mish",
                    [
                        INPUT,
                    ],
                    "Tensor",
                )
            ],
            "mish_": [
                defs(
                    "mish_",
                    [
                        INPUT,
                    ],
                    "Tensor",
                )
            ],
            "mse_loss": [
                defs(
                    "mse_loss",
                    [
                        INPUT,
                        "target: Tensor",
                        "reduction: str = ...",
                    ],
                    "Tensor",
                )
            ],
            "multilabel_margin_loss": [
                defs(
                    "multilabel_margin_loss",
                    [
                        INPUT,
                        "target: Tensor",
                        "reduction: str = ...",
                    ],
                    "Tensor",
                )
            ],
            "multi_margin_loss": [
                defs(
                    "multi_margin_loss",
                    [
                        INPUT,
                        "target: Tensor",
                        "p: float = 1.0",
                        "margin: float = 1.0",
                        "weight: Tensor | None = None",
                        "reduction: str = ...",
                    ],
                    "Tensor",
                )
            ],
            "nll_loss_nd": [
                defs(
                    "nll_loss_nd",
                    [
                        INPUT,
                        "target: Tensor",
                        "weight: Tensor | None = None",
                        "reduction: str = ...",
                        "ignore_index: int = -100",
                    ],
                    "Tensor",
                )
            ],
            "relu6": [
                defs(
                    "relu6",
                    [
                        INPUT,
                    ],
                    "Tensor",
                )
            ],
            "relu6_": [
                defs(
                    "relu6_",
                    [
                        INPUT,
                    ],
                    "Tensor",
                )
            ],
            "silu": [
                defs(
                    "silu",
                    [
                        INPUT,
                    ],
                    "Tensor",
                )
            ],
            "silu_": [
                defs(
                    "silu_",
                    [
                        INPUT,
                    ],
                    "Tensor",
                )
            ],
            "smooth_l1_loss": [
                defs(
                    "smooth_l1_loss",
                    [
                        INPUT,
                        "target: Tensor",
                        "reduction: str = ...",
                        "beta: float = 1.0",
                    ],
                    "Tensor",
                )
            ],
            "soft_margin_loss": [
                defs(
                    "soft_margin_loss",
                    [
                        INPUT,
                        "target: Tensor",
                        "reduction: str = ...",
                    ],
                    "Tensor",
                )
            ],
        }
    )

    c_nn_function_hints: list[str] = []
    for _, hints in sorted(unsorted_c_nn_function_hints.items()):
        if len(hints) > 1:
            hints = ["@overload\n" + h for h in hints]
        c_nn_function_hints += hints

    extra_nn_functional___all__: list[str] = []

    # Functions imported into `torch.nn.functional` from `torch`, perhaps being filtered
    # through an `_add_docstr` call
    torch_imports = [
        "adaptive_avg_pool1d",
        "avg_pool1d",
        "bilinear",
        "celu_",
        "channel_shuffle",
        "conv_tbc",
        "conv_transpose1d",
        "conv_transpose2d",
        "conv_transpose3d",
        "conv1d",
        "conv2d",
        "conv3d",
        "cosine_similarity",
        "hardshrink",
        "native_channel_shuffle",
        "pairwise_distance",
        "pdist",
        "pixel_shuffle",
        "pixel_unshuffle",
        "prelu",
        "relu_",
        "rrelu_",
        "selu_",
    ]
    imported_hints = [
        "from torch import (",
        *sorted(f"    {name} as {name}," for name in torch_imports),
        ")",
    ]
    extra_nn_functional___all__.extend(torch_imports)

    # Functions imported into `torch.nn.functional` from `torch._C._nn`
    c_nn_imports = [
        "avg_pool2d",
        "avg_pool3d",
        "elu_",
        "gelu",
        "hardtanh_",
        "leaky_relu_",
        "linear",
        "log_sigmoid",
        "one_hot",
        "pad",
        "scaled_dot_product_attention",
        "softplus",
        "softshrink",
    ]
    renamed = {"log_sigmoid": "logsigmoid"}
    imported_hints += [
        "from torch._C._nn import (",
        *sorted(f"    {name} as {renamed.get(name, name)}," for name in c_nn_imports),
        ")",
    ]
    extra_nn_functional___all__.extend(renamed.get(name, name) for name in c_nn_imports)

    # Functions generated by `torch._jit_internal.boolean_dispatch` in `nn.functional`
    unsorted_dispatched_hints: dict[str, list[str]] = {}

    for d in (1, 2, 3):
        unsorted_dispatched_hints.update(
            **get_max_pool_dispatch(
                f"max_pool{d}d",
                [
                    INPUT,
                    KERNEL_SIZE,
                    *STRIDE_PADDING,
                    "dilation: _int | _size = 1",
                    "ceil_mode: bool = False",
                    "{return_indices}",
                ],
            ),
            **get_max_pool_dispatch(
                f"fractional_max_pool{d}d",
                [
                    INPUT,
                    KERNEL_SIZE,
                    "output_size: _int | _size | None = None",
                    "output_ratio: _ratio_any_t | None = None",
                    "{return_indices}",
                    "_random_samples: Tensor | None = None",
                ],
            ),
            **get_max_pool_dispatch(
                f"adaptive_max_pool{d}d",
                [
                    INPUT,
                    "output_size: _int | _size",
                    "{return_indices}",
                ],
            ),
        )

    # There's no fractional_max_pool1d
    del unsorted_dispatched_hints["fractional_max_pool1d"]
    extra_nn_functional___all__.extend(unsorted_dispatched_hints)

    dispatched_hints: list[str] = []
    for _, hints in sorted(unsorted_dispatched_hints.items()):
        if len(hints) > 1:
            hints = ["@overload\n" + h for h in hints]
        dispatched_hints += hints

    extra_nn_functional___all__ = [
        "__all__ += [",
        *(f'    "{name}",' for name in extra_nn_functional___all__),
        "]",
    ]

    fm.write_with_template(
        "torch/nn/functional.pyi",
        "torch/nn/functional.pyi.in",
        lambda: {
            "imported_hints": imported_hints,
            "dispatched_hints": dispatched_hints,
            "extra_nn_functional___all__": extra_nn_functional___all__,
        },
    )
    fm.write_with_template(
        "torch/_C/_nn.pyi",
        "torch/_C/_nn.pyi.in",
        lambda: {
            "c_nn_function_hints": c_nn_function_hints,
        },
    )