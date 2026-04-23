def shard_on_the_fly(switch_checkpoint_path, dump_path, max_shard_size, dtype, weights_name: str = WEIGHTS_NAME):
    max_shard_size = convert_file_size_to_int(max_shard_size)
    sharded_state_dicts = []
    current_block = {}
    current_block_size = 0
    total_size = 0

    os.makedirs(dump_path, exist_ok=True)
    with gfile.GFile(switch_checkpoint_path + "/checkpoint", "rb") as fp:
        checkpoint_info = serialization.msgpack_restore(fp.read())["optimizer"]["target"]
        checkpoint_info = flatten_dict(checkpoint_info, sep="/")

    all_layers = {}
    for layer in checkpoint_info:
        curr_real_layer_name, split_layer, content = get_key_and_tensorstore_dict(
            layer, checkpoint_info, switch_checkpoint_path
        )
        if curr_real_layer_name in all_layers:
            all_layers[curr_real_layer_name][split_layer[-1]] = content
        else:
            all_layers[curr_real_layer_name] = {split_layer[-1]: content}

    for key, layer in all_layers.items():
        # open tensorstore file
        raw_weights = ts.open(unflatten_dict(layer)).result().read().result()
        raw_weights = torch.tensor(raw_weights)
        weight_size = raw_weights.numel() * raw_weights.element_size()

        # use the renaming pattern from the small conversion scripts
        key, raw_weights = rename_base_flax_keys(tuple(key.split("/")), raw_weights)
        key = "/".join(key)

        # If this weight is going to tip up over the maximal size, we split.
        if current_block_size + weight_size > max_shard_size:
            save_path = os.path.join(
                dump_path, weights_name.replace(".bin", f"-{len(sharded_state_dicts) + 1:05d}-of-???.bin")
            )
            rename_and_save_block(current_block, save_path)
            sharded_state_dicts.append(current_block.keys())
            del current_block
            current_block = {}
            current_block_size = 0

        current_block[key] = raw_weights.to(getattr(torch, dtype))
        current_block_size += weight_size
        total_size += weight_size

    # Add the last block
    save_path = os.path.join(
        dump_path, weights_name.replace(".bin", f"-{len(sharded_state_dicts) + 1:05d}-of-???.bin")
    )
    rename_and_save_block(current_block, save_path)
    sharded_state_dicts.append(current_block.keys())

    # If we only have one shard, we return it
    if len(sharded_state_dicts) == 1:
        return {weights_name: sharded_state_dicts[0]}, None

    # Otherwise, let's build the index
    weight_map = {}
    shards = {}
    for idx, shard in enumerate(sharded_state_dicts):
        shard_file = weights_name.replace(
            ".bin", f"-{idx + 1:05d}-of-{len(sharded_state_dicts):05d}.bin"
        )  # len(sharded_state_dicts):05d}
        temp_filename = os.path.join(dump_path, weights_name.replace(".bin", f"-{idx + 1:05d}-of-???.bin"))
        os.rename(temp_filename, os.path.join(dump_path, shard_file))
        shards[shard_file] = shard
        for key in shard:
            weight_map[key] = shard_file

    # Add the metadata
    metadata = {"total_size": total_size}
    index = {"metadata": metadata, "weight_map": weight_map}

    with open(os.path.join(dump_path, WEIGHTS_INDEX_NAME), "w", encoding="utf-8") as f:
        content = json.dumps(index, indent=2, sort_keys=True) + "\n"
        f.write(content)

    return metadata, index