def _read_pooling_mode(model_name, token):
        """
        Read the pooling mode from the modules.json file if it exists, otherwise return "mean".
        """
        try:
            if os.path.exists(model_name) and os.path.exists(
                os.path.join(model_name, "modules.json")
            ):
                modules_json_path = os.path.join(model_name, "modules.json")
            else:
                modules_json_path = hf_hub_download(
                    model_name, "modules.json", token = token
                )

            with open(modules_json_path, "r") as f:
                modules_config = json.load(f)

            pooling_config_path = None
            for module in modules_config:
                if module.get("type", "") == "sentence_transformers.models.Pooling":
                    pooling_path = module.get("path", "")
                    if pooling_path:
                        # try to find config.json for pooling module
                        if os.path.exists(model_name) and os.path.exists(
                            os.path.join(model_name, pooling_path, "config.json")
                        ):
                            pooling_config_path = os.path.join(
                                model_name, pooling_path, "config.json"
                            )
                        else:
                            pooling_config_path = hf_hub_download(
                                model_name,
                                os.path.join(pooling_path, "config.json"),
                                token = token,
                            )
                        break

            if pooling_config_path:
                with open(pooling_config_path, "r") as f:
                    pooling_config = json.load(f)
                    # from here:
                    # https://github.com/huggingface/sentence-transformers/blob/main/sentence_transformers/models/Pooling.py#L43
                    pooling_map = {
                        "pooling_mode_cls_token": "cls",
                        "pooling_mode_mean_tokens": "mean",
                        "pooling_mode_max_tokens": "max",
                        "pooling_mode_mean_sqrt_len_tokens": "mean_sqrt_len",
                        "pooling_mode_weightedmean_tokens": "weightedmean",
                        "pooling_mode_lasttoken": "lasttoken",
                    }
                    for config_key, mode in pooling_map.items():
                        if pooling_config.get(config_key):
                            if mode != "mean":
                                print(f"Pooling mode detected as {mode}, updating...")
                            return mode

        except Exception as e:
            print(
                f"Failed to detect pooling mode, not a sentence-transformers model. Using default pooling mode 'mean', this may or may not work."
            )
            return "mean"