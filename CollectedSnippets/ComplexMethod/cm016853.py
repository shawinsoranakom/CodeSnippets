def process_cond_list(d, prefix=""):
    if hasattr(d, "__iter__") and not hasattr(d, "items"):
        for index, item in enumerate(d):
            process_cond_list(item, f"{prefix}.{index}")
        return d
    elif hasattr(d, "items"):
        for k, v in list(d.items()):
            if isinstance(v, dict):
                process_cond_list(v, f"{prefix}.{k}")
            elif isinstance(v, torch.Tensor):
                d[k] = v.clone()
            elif isinstance(v, (list, tuple)):
                for index, item in enumerate(v):
                    process_cond_list(item, f"{prefix}.{k}.{index}")
    return d