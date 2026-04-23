def dump_infer_config(config, path, logger):
    setup_orderdict()
    infer_cfg = OrderedDict()
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    model_name = None
    if config["Global"].get("model_name", None):
        model_name = config["Global"]["model_name"]
        infer_cfg["Global"] = {"model_name": model_name}
    if config["Global"].get("uniform_output_enabled", True):
        arch_config = config["Architecture"]
        if arch_config["algorithm"] in ["SVTR_LCNet", "SVTR_HGNet"]:
            common_dynamic_shapes = {
                "x": [[1, 3, 48, 160], [1, 3, 48, 320], [8, 3, 48, 3200]]
            }
        elif arch_config["model_type"] == "det":
            common_dynamic_shapes = {
                "x": [[1, 3, 32, 32], [1, 3, 736, 736], [1, 3, 4000, 4000]]
            }
        elif arch_config["algorithm"] == "SLANet":
            if model_name == "SLANet_plus":
                common_dynamic_shapes = {
                    "x": [[1, 3, 32, 32], [1, 3, 64, 448], [1, 3, 488, 488]]
                }
            else:
                common_dynamic_shapes = {
                    "x": [[1, 3, 32, 32], [1, 3, 64, 448], [8, 3, 488, 488]]
                }
        elif arch_config["algorithm"] == "SLANeXt":
            common_dynamic_shapes = {
                "x": [[1, 3, 512, 512], [1, 3, 512, 512], [1, 3, 512, 512]]
            }
        elif arch_config["algorithm"] == "LaTeXOCR":
            common_dynamic_shapes = {
                "x": [[1, 1, 32, 32], [1, 1, 64, 448], [1, 1, 192, 672]]
            }
        elif arch_config["algorithm"] == "UniMERNet":
            common_dynamic_shapes = {
                "x": [[1, 1, 192, 672], [1, 1, 192, 672], [8, 1, 192, 672]]
            }
        elif arch_config["algorithm"] in ["PP-FormulaNet-L", "PP-FormulaNet_plus-L"]:
            common_dynamic_shapes = {
                "x": [[1, 1, 768, 768], [1, 1, 768, 768], [8, 1, 768, 768]]
            }
        elif arch_config["algorithm"] in [
            "PP-FormulaNet-S",
            "PP-FormulaNet_plus-S",
            "PP-FormulaNet_plus-M",
        ]:
            common_dynamic_shapes = {
                "x": [[1, 1, 384, 384], [1, 1, 384, 384], [8, 1, 384, 384]]
            }
        else:
            common_dynamic_shapes = None

        backend_keys = ["paddle_infer", "tensorrt"]
        hpi_config = {
            "backend_configs": {
                key: {
                    (
                        "dynamic_shapes" if key == "tensorrt" else "trt_dynamic_shapes"
                    ): common_dynamic_shapes
                }
                for key in backend_keys
            }
        }
        if common_dynamic_shapes:
            infer_cfg["Hpi"] = hpi_config

    infer_cfg["PreProcess"] = {"transform_ops": config["Eval"]["dataset"]["transforms"]}
    postprocess = OrderedDict()
    for k, v in config["PostProcess"].items():
        if config["Architecture"].get("algorithm") in [
            "LaTeXOCR",
            "UniMERNet",
            "PP-FormulaNet-L",
            "PP-FormulaNet-S",
            "PP-FormulaNet_plus-L",
            "PP-FormulaNet_plus-M",
            "PP-FormulaNet_plus-S",
        ]:
            if k != "rec_char_dict_path":
                postprocess[k] = v
        else:
            postprocess[k] = v

    if config["Architecture"].get("algorithm") in ["LaTeXOCR"]:
        tokenizer_file = config["Global"].get("rec_char_dict_path")
        if tokenizer_file is not None:
            with open(tokenizer_file, encoding="utf-8") as tokenizer_config_handle:
                character_dict = json.load(tokenizer_config_handle)
                postprocess["character_dict"] = character_dict
    elif config["Architecture"].get("algorithm") in [
        "UniMERNet",
        "PP-FormulaNet-L",
        "PP-FormulaNet-S",
        "PP-FormulaNet_plus-L",
        "PP-FormulaNet_plus-M",
        "PP-FormulaNet_plus-S",
    ]:
        tokenizer_file = config["Global"].get("rec_char_dict_path")
        fast_tokenizer_file = os.path.join(tokenizer_file, "tokenizer.json")
        tokenizer_config_file = os.path.join(tokenizer_file, "tokenizer_config.json")
        postprocess["character_dict"] = {}
        if fast_tokenizer_file is not None:
            with open(fast_tokenizer_file, encoding="utf-8") as tokenizer_config_handle:
                character_dict = json.load(tokenizer_config_handle)
                postprocess["character_dict"]["fast_tokenizer_file"] = character_dict
        if tokenizer_config_file is not None:
            with open(
                tokenizer_config_file, encoding="utf-8"
            ) as tokenizer_config_handle:
                character_dict = json.load(tokenizer_config_handle)
                postprocess["character_dict"]["tokenizer_config_file"] = character_dict
    else:
        if config["Global"].get("character_dict_path") is not None:
            with open(config["Global"]["character_dict_path"], encoding="utf-8") as f:
                lines = f.readlines()
                character_dict = [line.strip("\n") for line in lines]
            postprocess["character_dict"] = character_dict

    infer_cfg["PostProcess"] = postprocess

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(infer_cfg, f, default_flow_style=False, allow_unicode=True)
    logger.info("Export inference config file to {}".format(os.path.join(path)))