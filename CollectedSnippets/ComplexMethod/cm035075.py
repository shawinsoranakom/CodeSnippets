def dynamic_to_static(model, arch_config, logger, input_shape=None):
    if arch_config["algorithm"] == "SRN":
        max_text_length = arch_config["Head"]["max_text_length"]
        other_shape = [
            paddle.static.InputSpec(shape=[None, 1, 64, 256], dtype="float32"),
            [
                paddle.static.InputSpec(shape=[None, 256, 1], dtype="int64"),
                paddle.static.InputSpec(
                    shape=[None, max_text_length, 1], dtype="int64"
                ),
                paddle.static.InputSpec(
                    shape=[None, 8, max_text_length, max_text_length], dtype="int64"
                ),
                paddle.static.InputSpec(
                    shape=[None, 8, max_text_length, max_text_length], dtype="int64"
                ),
            ],
        ]
        model = to_static(model, input_spec=other_shape)
    elif arch_config["algorithm"] == "SAR":
        other_shape = [
            paddle.static.InputSpec(shape=[None, 3, 48, 160], dtype="float32"),
            [paddle.static.InputSpec(shape=[None], dtype="float32")],
        ]
        model = to_static(model, input_spec=other_shape)
    elif arch_config["algorithm"] in ["SVTR_LCNet", "SVTR_HGNet"]:
        other_shape = [
            paddle.static.InputSpec(shape=[None, 3, 48, -1], dtype="float32"),
        ]
        model = to_static(model, input_spec=other_shape)
    elif arch_config["algorithm"] in ["SVTR", "CPPD"]:
        other_shape = [
            paddle.static.InputSpec(shape=[None] + input_shape, dtype="float32"),
        ]
        model = to_static(model, input_spec=other_shape)
    elif arch_config["algorithm"] == "PREN":
        other_shape = [
            paddle.static.InputSpec(shape=[None, 3, 64, 256], dtype="float32"),
        ]
        model = to_static(model, input_spec=other_shape)
    elif arch_config["model_type"] == "sr":
        other_shape = [
            paddle.static.InputSpec(shape=[None, 3, 16, 64], dtype="float32")
        ]
        model = to_static(model, input_spec=other_shape)
    elif arch_config["algorithm"] == "ViTSTR":
        other_shape = [
            paddle.static.InputSpec(shape=[None, 1, 224, 224], dtype="float32"),
        ]
        model = to_static(model, input_spec=other_shape)
    elif arch_config["algorithm"] == "ABINet":
        if not input_shape:
            input_shape = [3, 32, 128]
        other_shape = [
            paddle.static.InputSpec(shape=[None] + input_shape, dtype="float32"),
        ]
        model = to_static(model, input_spec=other_shape)
    elif arch_config["algorithm"] in ["NRTR", "SPIN", "RFL"]:
        other_shape = [
            paddle.static.InputSpec(shape=[None, 1, 32, 100], dtype="float32"),
        ]
        model = to_static(model, input_spec=other_shape)
    elif arch_config["algorithm"] in ["SATRN"]:
        other_shape = [
            paddle.static.InputSpec(shape=[None, 3, 32, 100], dtype="float32"),
        ]
        model = to_static(model, input_spec=other_shape)
    elif arch_config["algorithm"] == "VisionLAN":
        other_shape = [
            paddle.static.InputSpec(shape=[None, 3, 64, 256], dtype="float32"),
        ]
        model = to_static(model, input_spec=other_shape)
    elif arch_config["algorithm"] == "RobustScanner":
        max_text_length = arch_config["Head"]["max_text_length"]
        other_shape = [
            paddle.static.InputSpec(shape=[None, 3, 48, 160], dtype="float32"),
            [
                paddle.static.InputSpec(
                    shape=[
                        None,
                    ],
                    dtype="float32",
                ),
                paddle.static.InputSpec(shape=[None, max_text_length], dtype="int64"),
            ],
        ]
        model = to_static(model, input_spec=other_shape)
    elif arch_config["algorithm"] == "CAN":
        other_shape = [
            [
                paddle.static.InputSpec(shape=[None, 1, None, None], dtype="float32"),
                paddle.static.InputSpec(shape=[None, 1, None, None], dtype="float32"),
                paddle.static.InputSpec(
                    shape=[None, arch_config["Head"]["max_text_length"]], dtype="int64"
                ),
            ]
        ]
        model = to_static(model, input_spec=other_shape)
    elif arch_config["algorithm"] == "LaTeXOCR":
        other_shape = [
            paddle.static.InputSpec(shape=[None, 1, None, None], dtype="float32"),
        ]
        model = to_static(model, input_spec=other_shape)
    elif arch_config["algorithm"] == "UniMERNet":
        model = paddle.jit.to_static(
            model,
            input_spec=[
                paddle.static.InputSpec(shape=[-1, 1, 192, 672], dtype="float32")
            ],
            full_graph=True,
        )
    elif arch_config["algorithm"] == "SLANeXt":
        model = paddle.jit.to_static(
            model,
            input_spec=[
                paddle.static.InputSpec(shape=[-1, 3, 512, 512], dtype="float32")
            ],
            full_graph=True,
        )
    elif arch_config["algorithm"] in ["PP-FormulaNet-L", "PP-FormulaNet_plus-L"]:
        model = paddle.jit.to_static(
            model,
            input_spec=[
                paddle.static.InputSpec(shape=[-1, 1, 768, 768], dtype="float32")
            ],
            full_graph=True,
        )
    elif arch_config["algorithm"] in [
        "PP-FormulaNet-S",
        "PP-FormulaNet_plus-S",
        "PP-FormulaNet_plus-M",
    ]:
        model = paddle.jit.to_static(
            model,
            input_spec=[
                paddle.static.InputSpec(shape=[-1, 1, 384, 384], dtype="float32")
            ],
            full_graph=True,
        )

    elif arch_config["algorithm"] in ["LayoutLM", "LayoutLMv2", "LayoutXLM"]:
        input_spec = [
            paddle.static.InputSpec(shape=[None, 512], dtype="int64"),  # input_ids
            paddle.static.InputSpec(shape=[None, 512, 4], dtype="int64"),  # bbox
            paddle.static.InputSpec(shape=[None, 512], dtype="int64"),  # attention_mask
            paddle.static.InputSpec(shape=[None, 512], dtype="int64"),  # token_type_ids
            paddle.static.InputSpec(shape=[None, 3, 224, 224], dtype="int64"),  # image
        ]
        if "Re" in arch_config["Backbone"]["name"]:
            input_spec.extend(
                [
                    paddle.static.InputSpec(
                        shape=[None, 512, 3], dtype="int64"
                    ),  # entities
                    paddle.static.InputSpec(
                        shape=[None, None, 2], dtype="int64"
                    ),  # relations
                ]
            )
        if model.backbone.use_visual_backbone is False:
            input_spec.pop(4)
        model = to_static(model, input_spec=[input_spec])
    else:
        infer_shape = [3, -1, -1]
        if arch_config["model_type"] == "rec":
            infer_shape = [3, 32, -1]  # for rec model, H must be 32
            if (
                "Transform" in arch_config
                and arch_config["Transform"] is not None
                and arch_config["Transform"]["name"] == "TPS"
            ):
                logger.info(
                    "When there is tps in the network, variable length input is not supported, and the input size needs to be the same as during training"
                )
                infer_shape[-1] = 100
        elif arch_config["model_type"] == "table":
            infer_shape = [3, 488, 488]
            if arch_config["algorithm"] == "TableMaster":
                infer_shape = [3, 480, 480]
            if arch_config["algorithm"] == "SLANet":
                infer_shape = [3, -1, -1]
        model = to_static(
            model,
            input_spec=[
                paddle.static.InputSpec(shape=[None] + infer_shape, dtype="float32")
            ],
        )

    if (
        arch_config["model_type"] != "sr"
        and arch_config["Backbone"]["name"] == "PPLCNetV3"
    ):
        # for rep lcnetv3
        for layer in model.sublayers():
            if hasattr(layer, "rep") and not getattr(layer, "is_repped"):
                layer.rep()
    return model