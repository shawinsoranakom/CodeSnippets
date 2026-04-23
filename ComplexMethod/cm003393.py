def replace_params(hf_params, tf_params, key_mapping):
    for key, value in tf_params.items():
        if "normalization" in key:
            continue

        hf_key = key_mapping[key]
        if "_conv" in key and "kernel" in key:
            new_hf_value = torch.from_numpy(value).permute(3, 2, 0, 1)
        elif "depthwise_kernel" in key:
            new_hf_value = torch.from_numpy(value).permute(2, 3, 0, 1)
        elif "kernel" in key:
            new_hf_value = torch.from_numpy(np.transpose(value))
        else:
            new_hf_value = torch.from_numpy(value)

        # Replace HF parameters with original TF model parameters
        assert hf_params[hf_key].shape == new_hf_value.shape
        hf_params[hf_key].copy_(new_hf_value)