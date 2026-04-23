def _canonicalize_to_arguments(a: Tensor, to_kwargs: dict):
    options_to_check = ["dtype", "device", "layout", "memory_format"]
    # "device" option could be passed a str instead torch.device
    if "device" in to_kwargs and isinstance(to_kwargs["device"], str):
        to_kwargs["device"] = torch.device(to_kwargs["device"])

    for kw in options_to_check:
        if kw in to_kwargs:
            if (
                (kw == "memory_format" and to_kwargs[kw] is torch.preserve_format)
                or (
                    kw == "device"
                    and to_kwargs[kw].type == a.device.type
                    and (
                        not to_kwargs[kw].index or to_kwargs[kw].index == a.device.index
                    )
                )
                or (
                    getattr(a, kw, None) == to_kwargs[kw]
                )  # this also handles {"memory_format": None}
            ):
                to_kwargs.pop(kw)