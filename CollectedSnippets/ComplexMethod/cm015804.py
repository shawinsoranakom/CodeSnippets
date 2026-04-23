def build_opt_kwarg_db():
    compiled_opt_db = []
    for optim_info in optim_db:
        if optim_info.optim_cls not in KERNEL_COUNTS:
            continue

        for device in ["cpu", GPU_TYPE]:
            for optim_inputs in _get_optim_inputs_including_global_cliquey_kwargs(
                device, None, optim_info, skip=("differentiable", "fused")
            ):
                kwargs = dict(optim_inputs.kwargs)
                name = f"test_{optim_info.optim_cls.__name__.lower()}"

                has_tensor_lr = False
                for key, val in kwargs.items():
                    if (key != "lr" and key != "betas") and (
                        not isinstance(val, bool) or (isinstance(val, bool) and val)
                    ):
                        name += "_" + key

                    if key == "lr" and isinstance(kwargs["lr"], torch.Tensor):
                        has_tensor_lr = True
                        name += "_tensor_lr"

                    if key == "betas" and isinstance(kwargs["betas"][0], torch.Tensor):
                        name += "_tensor_betas"

                name += f"_{device}"

                kwargs["device"] = device
                if name in KERNEL_COUNT_OVERRIDES:
                    kwargs["kernel_count"] = KERNEL_COUNT_OVERRIDES[name]
                else:
                    kwargs["kernel_count"] = (
                        KERNEL_COUNTS[optim_info.optim_cls].multitensor
                        if kwargs.get("foreach", False) and device == GPU_TYPE
                        else KERNEL_COUNTS[optim_info.optim_cls].singletensor
                    )

                if kwargs["kernel_count"] is None or kwargs.get("fused", False):
                    continue

                if has_tensor_lr:
                    for scheduler_cls in LR_SCHEDULER_TO_KWARGS:
                        name_w_scheduler = name + f"_{scheduler_cls.__name__.lower()}"
                        compiled_opt_db.append(
                            (
                                optim_info.optim_cls,
                                name_w_scheduler,
                                kwargs,
                                scheduler_cls,
                            )
                        )
                else:
                    compiled_opt_db.append((optim_info.optim_cls, name, kwargs, None))

    return compiled_opt_db