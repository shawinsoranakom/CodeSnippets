def convert_bloom_checkpoint_to_pytorch(
    bloom_checkpoint_path, bloom_config_file, pytorch_dump_folder_path, shard_model, pretraining_tp
):
    # Construct model
    if bloom_config_file == "":
        config = BloomConfig()
    else:
        config = BloomConfig.from_json_file(bloom_config_file)

    if shard_model:
        file_names = os.listdir(bloom_checkpoint_path)
        file_names = sorted(filter(lambda s: s.startswith("layer") and "model_00" in s, file_names))

        index_dict = {"weight_map": {}, "metadata": {}}
        total_size = 0

        missing_keys = None

        config = BloomConfig()

        for j, file in enumerate(file_names):
            print(f"Processing file: {file}")
            tensors = None

            for i in range(pretraining_tp):
                # load all TP files
                f_name = file.replace("model_00", f"model_0{i}")
                temp = torch.load(os.path.join(bloom_checkpoint_path, f_name), map_location="cpu", weights_only=True)

                # Rename keys in the transformers names
                keys = list(temp.keys())
                for key in keys:
                    temp[layer_name_mapping(key, file)] = temp.pop(key)

                if tensors is None:
                    tensors = temp
                else:
                    for key in tensors:
                        if any(key.endswith(end) for end in WEIGHTS_TO_AVERAGE_ENDSWITH):
                            # We average (sum and then divide) some weights across TP ranks (see https://github.com/bigscience-workshop/Megatron-DeepSpeed/blob/olruwase/sync_layer_norms/megatron/training.py#L425)
                            tensors[key] += temp[key]
                        else:
                            # Some weights are RowParallelLinear in Megatron-Deepspeed, others are ColumnParallel
                            cat_dim = 1 if any(text in key for text in WEIGHTS_WITH_ROW_PARALLELISM_CONTAIN) else 0
                            # We concatenate these weights across TP ranks
                            tensors[key] = torch.cat([tensors[key], temp[key]], dim=cat_dim)

            # Divide by the number of TP the weights we want to average
            for key in tensors:
                if any(key.endswith(end) for end in WEIGHTS_TO_AVERAGE_ENDSWITH):
                    tensors[key] = tensors[key] / pretraining_tp
            torch.save(
                tensors,
                os.path.join(
                    pytorch_dump_folder_path,
                    f"pytorch_model_{str(j + 1).zfill(5)}-of-{str(len(file_names)).zfill(5)}.bin",
                ),
            )

            for key in tensors:
                value = tensors[key]
                total_size += value.numel() * get_dtype_size(value.dtype)
                if key not in index_dict["weight_map"]:
                    index_dict["weight_map"][key] = (
                        f"pytorch_model_{str(j + 1).zfill(5)}-of-{str(len(file_names)).zfill(5)}.bin"
                    )

        config = BloomConfig()
        pytorch_config_dump_path = pytorch_dump_folder_path + "/" + CONFIG_NAME
        index_dict["metadata"]["total_size"] = total_size
        with open(pytorch_config_dump_path, "w", encoding="utf-8") as f:
            f.write(config.to_json_string())
        with open(os.path.join(pytorch_dump_folder_path, WEIGHTS_NAME + ".index.json"), "w", encoding="utf-8") as f:
            json_config = json.dumps(index_dict, indent=2, sort_keys=True) + "\n"
            f.write(json_config)
    else:
        model = BloomModel(config)

        file_names = os.listdir(bloom_checkpoint_path)
        file_names = sorted(filter(lambda s: s.startswith("layer") and "model_00" in s, file_names))

        missing_keys = None
        for i, file in enumerate(file_names):
            tensors = None
            for i in range(pretraining_tp):
                # load all TP files
                f_name = file.replace("model_00", f"model_0{i}")
                temp = torch.load(os.path.join(bloom_checkpoint_path, f_name), map_location="cpu", weights_only=True)

                # Rename keys in the transformers names
                keys = list(temp.keys())
                for key in keys:
                    temp[layer_name_mapping(key, file)] = temp.pop(key)

                if tensors is None:
                    tensors = temp
                else:
                    for key in tensors:
                        # We average (sum and then divide) some weights across TP ranks (see https://github.com/bigscience-workshop/Megatron-DeepSpeed/blob/olruwase/sync_layer_norms/megatron/training.py#L425)
                        if any(key.endswith(end) for end in WEIGHTS_TO_AVERAGE_ENDSWITH):
                            tensors[key] += temp[key]
                        else:
                            # Some weights are RowParallelLinear in Megatron-Deepspeed, others are ColumnParallel
                            cat_dim = 1 if any(text in key for text in WEIGHTS_WITH_ROW_PARALLELISM_CONTAIN) else 0
                            # We concatenate these weights across TP ranks
                            tensors[key] = torch.cat([tensors[key], temp[key]], dim=cat_dim)

            # Divide by the number of TP the weights we want to average
            for key in tensors:
                if any(key.endswith(end) for end in WEIGHTS_TO_AVERAGE_ENDSWITH):
                    tensors[key] = tensors[key] / pretraining_tp

            other_keys = model.load_state_dict(tensors, strict=False)
            assert not other_keys.unexpected_keys, f"The keys {other_keys.unexpected_keys} are unexpected"
            if missing_keys is None:
                missing_keys = set(other_keys.missing_keys)
            else:
                missing_keys = missing_keys.intersection(set(other_keys.missing_keys))

        assert not missing_keys, f"The keys {missing_keys} are missing"

        # Save pytorch-model
        os.makedirs(pytorch_dump_folder_path, exist_ok=True)
        pytorch_weights_dump_path = pytorch_dump_folder_path + "/" + WEIGHTS_NAME
        pytorch_config_dump_path = pytorch_dump_folder_path + "/" + CONFIG_NAME
        print(f"Save PyTorch model to {pytorch_weights_dump_path} with dtype {config.dtype}")
        if config.dtype is not None:
            model = model.to(config.dtype)
        torch.save(model.state_dict(), pytorch_weights_dump_path)
        print(f"Save configuration file to {pytorch_config_dump_path}")
        with open(pytorch_config_dump_path, "w", encoding="utf-8") as f:
            f.write(config.to_json_string())