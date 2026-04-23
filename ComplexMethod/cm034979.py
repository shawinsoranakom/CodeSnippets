def apply_to_static(model, config, logger):
    if config["Global"].get("to_static", False) is not True:
        return model
    assert (
        "d2s_train_image_shape" in config["Global"]
    ), "d2s_train_image_shape must be assigned for static training mode..."
    supported_list = [
        "DB",
        "SVTR_LCNet",
        "TableMaster",
        "LayoutXLM",
        "SLANet",
        "SVTR",
        "SVTR_HGNet",
        "LaTeXOCR",
        "UniMERNet",
        "PP-FormulaNet-S",
        "PP-FormulaNet-L",
    ]
    if config["Architecture"]["algorithm"] in ["Distillation"]:
        algo = list(config["Architecture"]["Models"].values())[0]["algorithm"]
    else:
        algo = config["Architecture"]["algorithm"]
    assert (
        algo in supported_list
    ), f"algorithms that supports static training must in in {supported_list} but got {algo}"

    specs = [
        InputSpec([None] + config["Global"]["d2s_train_image_shape"], dtype="float32")
    ]

    if algo == "SVTR_LCNet":
        specs.append(
            [
                InputSpec([None, config["Global"]["max_text_length"]], dtype="int64"),
                InputSpec([None, config["Global"]["max_text_length"]], dtype="int64"),
                InputSpec([None], dtype="int64"),
                InputSpec([None], dtype="float64"),
            ]
        )
    elif algo == "TableMaster":
        specs.append(
            [
                InputSpec([None, config["Global"]["max_text_length"]], dtype="int64"),
                InputSpec(
                    [None, config["Global"]["max_text_length"], 4], dtype="float32"
                ),
                InputSpec(
                    [None, config["Global"]["max_text_length"], 1], dtype="float32"
                ),
                InputSpec([None, 6], dtype="float32"),
            ]
        )
    elif algo == "LayoutXLM":
        specs = [
            [
                InputSpec(shape=[None, 512], dtype="int64"),  # input_ids
                InputSpec(shape=[None, 512, 4], dtype="int64"),  # bbox
                InputSpec(shape=[None, 512], dtype="int64"),  # attention_mask
                InputSpec(shape=[None, 512], dtype="int64"),  # token_type_ids
                InputSpec(shape=[None, 3, 224, 224], dtype="float32"),  # image
                InputSpec(shape=[None, 512], dtype="int64"),  # label
            ]
        ]
    elif algo == "SLANet":
        specs.append(
            [
                InputSpec(
                    [None, config["Global"]["max_text_length"] + 2], dtype="int64"
                ),
                InputSpec(
                    [None, config["Global"]["max_text_length"] + 2, 4], dtype="float32"
                ),
                InputSpec(
                    [None, config["Global"]["max_text_length"] + 2, 1], dtype="float32"
                ),
                InputSpec([None], dtype="int64"),
                InputSpec([None, 6], dtype="float64"),
            ]
        )
    elif algo == "SVTR":
        specs.append(
            [
                InputSpec([None, config["Global"]["max_text_length"]], dtype="int64"),
                InputSpec([None], dtype="int64"),
            ]
        )
    elif algo == "LaTeXOCR":
        specs = [
            [
                InputSpec(shape=[None, 1, None, None], dtype="float32"),
                InputSpec(shape=[None, None], dtype="float32"),
                InputSpec(shape=[None, None], dtype="float32"),
            ]
        ]
    elif algo in ["UniMERNet", "PP-FormulaNet-S", "PP-FormulaNet-L"]:
        specs = [
            [
                InputSpec(
                    [None] + config["Global"]["d2s_train_image_shape"], dtype="float32"
                ),
                InputSpec(shape=[None, None], dtype="float32"),
                InputSpec(shape=[None, None], dtype="float32"),
            ]
        ]
    model = to_static(model, input_spec=specs)
    logger.info("Successfully to apply @to_static with specs: {}".format(specs))
    return model