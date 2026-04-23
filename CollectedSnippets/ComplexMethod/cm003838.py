def replace_params(hf_params, tf_params, key_mapping):
    list(hf_params.keys())

    for key, value in tf_params.items():
        if key not in key_mapping:
            continue

        hf_key = key_mapping[key]
        if "_conv" in key and "kernel" in key:
            new_hf_value = torch.from_numpy(value).permute(3, 2, 0, 1)
        elif "embeddings" in key:
            new_hf_value = torch.from_numpy(value)
        elif "depthwise_kernel" in key:
            new_hf_value = torch.from_numpy(value).permute(2, 3, 0, 1)
        elif "kernel" in key:
            new_hf_value = torch.from_numpy(np.transpose(value))
        elif "temperature" in key:
            new_hf_value = value
        elif "bn/gamma" in key or "bn/beta" in key:
            new_hf_value = torch.from_numpy(np.transpose(value)).squeeze()
        else:
            new_hf_value = torch.from_numpy(value)

        # Replace HF parameters with original TF model parameters
        hf_params[hf_key].copy_(new_hf_value)