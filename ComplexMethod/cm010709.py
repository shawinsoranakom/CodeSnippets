def use_mkldnn(input, hx, params):
        if not torch._C._get_mkldnn_enabled():
            return False

        tensors = [input] + list(hx) + list(chain.from_iterable(params))
        devices = {t.device for t in tensors}
        if len(devices) != 1:
            return False

        device = devices.pop()
        if device != torch.device("cpu"):
            return False
        # With autocast, possible to have mixed dtype here
        dtypes = {t.dtype for t in tensors}
        for dtype in dtypes:
            if dtype not in [torch.float, torch.bfloat16]:
                return False

        if input.requires_grad:
            return False

        has_projections = hx[0].size(2) != hx[1].size(2)
        if has_projections:
            return False

        return True