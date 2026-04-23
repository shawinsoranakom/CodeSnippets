def _read_h5_weights(group, current_key="", weights=None):
    if weights is None:
        weights = {}
    for key in group:
        full_key = f"{current_key}.{key}" if current_key else key
        if isinstance(group[key], h5py.Dataset):
            w = np.array(group[key])
            w = torch.from_numpy(w)
            if len(w.shape) > 1:
                if len(w.shape) == 3:
                    hidden_size = max(list(w.shape))
                    try:
                        w = w.reshape(hidden_size, hidden_size)
                    except RuntimeError:
                        # meaning its a conv layers
                        pass
                w = w.transpose(0, -1)
            weights[full_key] = w
        else:
            _read_h5_weights(group[key], full_key, weights)
    return weights