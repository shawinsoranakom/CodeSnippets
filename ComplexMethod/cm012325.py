def fn(match):
        assert all(k in match.kwargs for k in ("x", "weight", "scales"))
        if not all(
            hasattr(match.kwargs[key], "meta") for key in ["x", "weight", "scales"]
        ):
            return False
        x = match.kwargs["x"].meta["val"]
        weight = match.kwargs["weight"].meta["val"]
        scales = match.kwargs["scales"].meta["val"]
        return (
            # For now, we only support woq mm kernels
            # with x.type=bfloat16 and w.type=int8
            x.dtype == torch.bfloat16
            and weight.dtype == torch.int8
            and scales.dtype == torch.bfloat16
            and x.device.type in ("cpu", "cuda", "xpu")
            and x.device == weight.device
            and x.device == scales.device
        )