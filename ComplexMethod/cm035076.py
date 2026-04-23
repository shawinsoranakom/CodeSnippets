def export(config, base_model=None, save_path=None):
    if paddle.distributed.get_rank() != 0:
        return
    logger = get_logger()
    # build post process
    post_process_class = build_post_process(config["PostProcess"], config["Global"])

    # build model
    # for rec algorithm
    if hasattr(post_process_class, "character"):
        char_num = len(getattr(post_process_class, "character"))
        if config["Architecture"]["algorithm"] in [
            "Distillation",
        ]:  # distillation model
            for key in config["Architecture"]["Models"]:
                if (
                    config["Architecture"]["Models"][key]["Head"]["name"] == "MultiHead"
                ):  # multi head
                    out_channels_list = {}
                    if config["PostProcess"]["name"] == "DistillationSARLabelDecode":
                        char_num = char_num - 2
                    if config["PostProcess"]["name"] == "DistillationNRTRLabelDecode":
                        char_num = char_num - 3
                    out_channels_list["CTCLabelDecode"] = char_num
                    out_channels_list["SARLabelDecode"] = char_num + 2
                    out_channels_list["NRTRLabelDecode"] = char_num + 3
                    config["Architecture"]["Models"][key]["Head"][
                        "out_channels_list"
                    ] = out_channels_list
                else:
                    config["Architecture"]["Models"][key]["Head"][
                        "out_channels"
                    ] = char_num
                # just one final tensor needs to exported for inference
                config["Architecture"]["Models"][key]["return_all_feats"] = False
        elif config["Architecture"]["Head"]["name"] == "MultiHead":  # multi head
            out_channels_list = {}
            char_num = len(getattr(post_process_class, "character"))
            if config["PostProcess"]["name"] == "SARLabelDecode":
                char_num = char_num - 2
            if config["PostProcess"]["name"] == "NRTRLabelDecode":
                char_num = char_num - 3
            out_channels_list["CTCLabelDecode"] = char_num
            out_channels_list["SARLabelDecode"] = char_num + 2
            out_channels_list["NRTRLabelDecode"] = char_num + 3
            config["Architecture"]["Head"]["out_channels_list"] = out_channels_list
        else:  # base rec model
            config["Architecture"]["Head"]["out_channels"] = char_num

    # for sr algorithm
    if config["Architecture"]["model_type"] == "sr":
        config["Architecture"]["Transform"]["infer_mode"] = True

    # for latexocr algorithm
    if config["Architecture"].get("algorithm") in ["LaTeXOCR"]:
        config["Architecture"]["Backbone"]["is_predict"] = True
        config["Architecture"]["Backbone"]["is_export"] = True
        config["Architecture"]["Head"]["is_export"] = True
    if config["Architecture"].get("algorithm") in ["UniMERNet"]:
        config["Architecture"]["Backbone"]["is_export"] = True
        config["Architecture"]["Head"]["is_export"] = True
    if config["Architecture"].get("algorithm") in [
        "PP-FormulaNet-S",
        "PP-FormulaNet-L",
        "PP-FormulaNet_plus-S",
        "PP-FormulaNet_plus-M",
        "PP-FormulaNet_plus-L",
    ]:
        config["Architecture"]["Head"]["is_export"] = True
    if base_model is not None:
        model = base_model
        if isinstance(model, paddle.DataParallel):
            model = copy.deepcopy(model._layers)
        else:
            model = copy.deepcopy(model)
    else:
        model = build_model(config["Architecture"])
        load_model(config, model, model_type=config["Architecture"]["model_type"])
    convert_bn(model)
    model.eval()

    if not save_path:
        save_path = config["Global"]["save_inference_dir"]
    yaml_path = os.path.join(save_path, "inference.yml")

    arch_config = config["Architecture"]

    if (
        arch_config["algorithm"] in ["SVTR", "CPPD"]
        and arch_config["Head"]["name"] != "MultiHead"
    ):
        input_shape = config["Eval"]["dataset"]["transforms"][-2]["SVTRRecResizeImg"][
            "image_shape"
        ]
    elif arch_config["algorithm"].lower() == "ABINet".lower():
        rec_rs = [
            c
            for c in config["Eval"]["dataset"]["transforms"]
            if "ABINetRecResizeImg" in c
        ]
        input_shape = rec_rs[0]["ABINetRecResizeImg"]["image_shape"] if rec_rs else None
    else:
        input_shape = None
    dump_infer_config(config, yaml_path, logger)
    if arch_config["algorithm"] in [
        "Distillation",
    ]:  # distillation model
        archs = list(arch_config["Models"].values())
        for idx, name in enumerate(model.model_name_list):
            sub_model_save_path = os.path.join(save_path, name, "inference")
            export_single_model(
                model.model_list[idx],
                archs[idx],
                sub_model_save_path,
                logger,
                yaml_path,
                config,
            )
    else:
        save_path = os.path.join(save_path, "inference")
        export_single_model(
            model,
            arch_config,
            save_path,
            logger,
            yaml_path,
            config,
            input_shape=input_shape,
        )