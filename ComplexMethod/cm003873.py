def load_weights(input_dir: str):
    safetensor_files = [os.path.join(input_dir, x) for x in os.listdir(input_dir) if x.endswith(".safetensors")]
    bin_files = [os.path.join(input_dir, x) for x in os.listdir(input_dir) if x.endswith(".bin")]

    all_weights = {}

    if safetensor_files:
        safetensor_files = sorted(safetensor_files, key=lambda x: int(x.rsplit("-", 3)[1]))
        for file in safetensor_files:
            tensors = load_file(file)
            all_weights.update(tensors)
        return all_weights

    elif bin_files:
        bin_files = sorted(bin_files, key=lambda x: int(x.rsplit("-", 3)[1]))
        for file in bin_files:
            tensors = torch.load(file, map_location="cpu", weights_only=True)
            all_weights.update(tensors)
        return all_weights

    else:
        raise ValueError("No .safetensors or .bin files found in the specified directory.")