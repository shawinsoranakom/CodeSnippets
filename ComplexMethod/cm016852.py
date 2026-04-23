def make_batch_extra_option_dict(d, indicies, full_size=None):
    new_dict = {}
    for k, v in d.items():
        newv = v
        if isinstance(v, dict):
            newv = make_batch_extra_option_dict(v, indicies, full_size=full_size)
        elif isinstance(v, torch.Tensor):
            if full_size is None or v.size(0) == full_size:
                newv = v[indicies]
        elif isinstance(v, (list, tuple)) and len(v) == full_size:
            newv = [v[i] for i in indicies]
        new_dict[k] = newv
    return new_dict