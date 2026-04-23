def _pad(items, key, padding_value, padding_side):
    batch_size = len(items)
    if isinstance(items[0][key], torch.Tensor):
        # Others include `attention_mask` etc...
        shape = items[0][key].shape
        dim = items[0][key].ndim
        if dim == 1:
            # We have a list of 1-dim torch tensors, which can be stacked without padding
            return torch.cat([item[key] for item in items], dim=0)
        if key in ["pixel_values", "image"]:
            # This is probable image so padding shouldn't be necessary
            # B, C, H, W
            return torch.cat([item[key] for item in items], dim=0)
        elif dim == 4 and key == "input_features":
            # this is probably a mel spectrogram batched
            return torch.cat([item[key] for item in items], dim=0)
        max_length = max(item[key].shape[1] for item in items)
        min_length = min(item[key].shape[1] for item in items)
        dtype = items[0][key].dtype

        if dim == 2 and max_length == min_length:
            # Bypass for `ImageGPT` which doesn't provide a padding value, yet
            # we can consistently pad since the size should be matching
            return torch.cat([item[key] for item in items], dim=0)
        else:
            tensor = torch.full([batch_size, max_length] + list(shape[2:]), fill_value=padding_value, dtype=dtype)

        for i, item in enumerate(items):
            if padding_side == "left":
                tensor[i, -len(item[key][0]) :] = item[key][0]
            else:
                tensor[i, : len(item[key][0])] = item[key][0]

        return tensor
    else:
        return [item[key] for item in items]