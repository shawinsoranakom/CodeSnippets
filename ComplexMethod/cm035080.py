def update_train_results(config, prefix, metric_info, done_flag=False, last_num=5):
    if paddle.distributed.get_rank() != 0:
        return

    assert last_num >= 1
    train_results_path = os.path.join(
        config["Global"]["save_model_dir"], "train_result.json"
    )
    save_model_tag = ["pdparams", "pdopt", "pdstates"]
    paddle_version = version.parse(paddle.__version__)
    if FLAGS_json_format_model or paddle_version >= version.parse("3.0.0"):
        save_inference_files = {
            "inference_config": "inference.yml",
            "pdmodel": "inference.json",
            "pdiparams": "inference.pdiparams",
        }
    else:
        save_inference_files = {
            "inference_config": "inference.yml",
            "pdmodel": "inference.pdmodel",
            "pdiparams": "inference.pdiparams",
            "pdiparams.info": "inference.pdiparams.info",
        }
    if os.path.exists(train_results_path):
        with open(train_results_path, "r") as fp:
            train_results = json.load(fp)
    else:
        train_results = {}
        train_results["model_name"] = config["Global"]["model_name"]
        label_dict_path = config["Global"].get("character_dict_path", "")
        if label_dict_path != "":
            label_dict_path = os.path.abspath(label_dict_path)
            if not os.path.exists(label_dict_path):
                label_dict_path = ""
        train_results["label_dict"] = label_dict_path
        train_results["train_log"] = "train.log"
        train_results["visualdl_log"] = ""
        train_results["config"] = "config.yaml"
        train_results["models"] = {}
        for i in range(1, last_num + 1):
            train_results["models"][f"last_{i}"] = {}
        train_results["models"]["best"] = {}
    train_results["done_flag"] = done_flag
    if "best" in prefix:
        if "acc" in metric_info["metric"]:
            metric_score = metric_info["metric"]["acc"]
        elif "precision" in metric_info["metric"]:
            metric_score = metric_info["metric"]["precision"]
        elif "exp_rate" in metric_info["metric"]:
            metric_score = metric_info["metric"]["exp_rate"]
        else:
            raise ValueError("No metric score found.")
        train_results["models"]["best"]["score"] = metric_score
        for tag in save_model_tag:
            if tag == "pdparams" and encrypted:
                train_results["models"]["best"][tag] = os.path.join(
                    prefix,
                    (
                        f"{prefix}.encrypted.{tag}"
                        if tag != "pdstates"
                        else f"{prefix}.states"
                    ),
                )
            else:
                train_results["models"]["best"][tag] = os.path.join(
                    prefix,
                    f"{prefix}.{tag}" if tag != "pdstates" else f"{prefix}.states",
                )
        for key in save_inference_files:
            train_results["models"]["best"][key] = os.path.join(
                prefix, "inference", save_inference_files[key]
            )
    else:
        for i in range(last_num - 1, 0, -1):
            train_results["models"][f"last_{i + 1}"] = train_results["models"][
                f"last_{i}"
            ].copy()
        if "acc" in metric_info["metric"]:
            metric_score = metric_info["metric"]["acc"]
        elif "precision" in metric_info["metric"]:
            metric_score = metric_info["metric"]["precision"]
        elif "exp_rate" in metric_info["metric"]:
            metric_score = metric_info["metric"]["exp_rate"]
        else:
            metric_score = 0
        train_results["models"][f"last_{1}"]["score"] = metric_score
        for tag in save_model_tag:
            if tag == "pdparams" and encrypted:
                train_results["models"][f"last_{1}"][tag] = os.path.join(
                    prefix,
                    (
                        f"{prefix}.encrypted.{tag}"
                        if tag != "pdstates"
                        else f"{prefix}.states"
                    ),
                )
            else:
                train_results["models"][f"last_{1}"][tag] = os.path.join(
                    prefix,
                    f"{prefix}.{tag}" if tag != "pdstates" else f"{prefix}.states",
                )
        for key in save_inference_files:
            train_results["models"][f"last_{1}"][key] = os.path.join(
                prefix, "inference", save_inference_files[key]
            )

    with open(train_results_path, "w") as fp:
        json.dump(train_results, fp)