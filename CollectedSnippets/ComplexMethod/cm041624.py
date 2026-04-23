def save_weight(input_dir: str, output_dir: str, shard_size: str, save_safetensors: bool):
    baichuan2_state_dict: dict[str, torch.Tensor] = OrderedDict()
    for filepath in tqdm(os.listdir(input_dir), desc="Load weights"):
        if os.path.isfile(os.path.join(input_dir, filepath)) and filepath.endswith(".bin"):
            shard_weight = torch.load(os.path.join(input_dir, filepath), map_location="cpu", weights_only=True)
            baichuan2_state_dict.update(shard_weight)

    llama_state_dict: dict[str, torch.Tensor] = OrderedDict()
    for key, value in tqdm(baichuan2_state_dict.items(), desc="Convert format"):
        if "W_pack" in key:
            proj_size = value.size(0) // 3
            llama_state_dict[key.replace("W_pack", "q_proj")] = value[:proj_size, :]
            llama_state_dict[key.replace("W_pack", "k_proj")] = value[proj_size : 2 * proj_size, :]
            llama_state_dict[key.replace("W_pack", "v_proj")] = value[2 * proj_size :, :]
        elif "lm_head" in key:
            llama_state_dict[key] = torch.nn.functional.normalize(value)
        else:
            llama_state_dict[key] = value

    weights_name = SAFE_WEIGHTS_NAME if save_safetensors else WEIGHTS_NAME
    filename_pattern = weights_name.replace(".bin", "{suffix}.bin").replace(".safetensors", "{suffix}.safetensors")
    state_dict_split = split_torch_state_dict_into_shards(
        llama_state_dict, filename_pattern=filename_pattern, max_shard_size=shard_size
    )
    for shard_file, tensors in tqdm(state_dict_split.filename_to_tensors.items(), desc="Save weights"):
        shard = {tensor: llama_state_dict[tensor].contiguous() for tensor in tensors}
        if save_safetensors:
            save_file(shard, os.path.join(output_dir, shard_file), metadata={"format": "pt"})
        else:
            torch.save(shard, os.path.join(output_dir, shard_file))

    if not state_dict_split.is_sharded:
        print(f"Model weights saved in {os.path.join(output_dir, weights_name)}.")
    else:
        index = {
            "metadata": state_dict_split.metadata,
            "weight_map": state_dict_split.tensor_to_filename,
        }
        index_name = SAFE_WEIGHTS_INDEX_NAME if save_safetensors else WEIGHTS_INDEX_NAME
        with open(os.path.join(output_dir, index_name), "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, sort_keys=True)

        print(f"Model weights saved in {output_dir}.")