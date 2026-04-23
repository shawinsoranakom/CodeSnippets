def save_weights_to_safetensors(
    weights: dict[str, torch.Tensor], output_path: Path
) -> None:
    """Save weights to safetensors files and create index."""

    # Determine how to shard the weights
    max_shard_size = 5 * 1024 * 1024 * 1024  # 5GB per shard

    # Calculate sizes and create shards
    shards = []
    current_shard: dict[str, torch.Tensor] = {}
    current_size = 0

    for name, tensor in weights.items():
        tensor_size = tensor.numel() * tensor.element_size()

        if current_size + tensor_size > max_shard_size and current_shard:
            shards.append(current_shard)
            current_shard = {}
            current_size = 0

        current_shard[name] = tensor
        current_size += tensor_size

    if current_shard:
        shards.append(current_shard)

    # Save shards and create index
    weight_map = {}

    if len(shards) == 1:
        # Single file
        filename = "model.safetensors"
        save_file(shards[0], output_path / filename)
        weight_map = {name: filename for name in shards[0]}
        print(f"Saved weights to single file: {filename}")
    else:
        # Multiple shards
        for i, shard in enumerate(shards):
            filename = f"model-{i + 1:05d}-of-{len(shards):05d}.safetensors"
            save_file(shard, output_path / filename)
            for name in shard:
                weight_map[name] = filename
            print(f"Saved shard {i + 1}/{len(shards)}: {filename}")

    # Create index file
    index_data = {
        "metadata": {
            "total_size": sum(
                tensor.numel() * tensor.element_size() for tensor in weights.values()
            )
        },
        "weight_map": weight_map,
    }

    index_path = output_path / "model.safetensors.index.json"
    with open(index_path, "w") as f:
        json.dump(index_data, f, indent=2)

    print(f"Created index file: {index_path}")
    print(
        f"Total model size: {index_data['metadata']['total_size'] / (1024**3):.2f} GB"
    )