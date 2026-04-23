def apply_model(orig_func, self, x_noisy, t, cond, **kwargs):
    """Always make sure inputs to unet are in correct dtype."""
    if isinstance(cond, dict):
        for y in cond.keys():
            if isinstance(cond[y], list):
                cond[y] = [x.to(devices.dtype_unet) if isinstance(x, torch.Tensor) else x for x in cond[y]]
            else:
                cond[y] = cond[y].to(devices.dtype_unet) if isinstance(cond[y], torch.Tensor) else cond[y]

    with devices.autocast():
        result = orig_func(self, x_noisy.to(devices.dtype_unet), t.to(devices.dtype_unet), cond, **kwargs)
        if devices.unet_needs_upcast:
            return result.float()
        else:
            return result