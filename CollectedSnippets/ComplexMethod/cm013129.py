def wrapped(*args, **kwargs):
            kwargs.update(zip(arg_names, args, strict=False))
            cond = True
            if "device" in kwargs:
                cond = cond and (torch.device(kwargs["device"]).type == "cpu")
            if "dtype" in kwargs:
                cond = cond and (kwargs["dtype"] == torch.float)
            bf32_cond = cond and bf32_is_not_fp32()
            tf32_cond = cond and tf32_is_not_fp32()
            if bf32_cond or tf32_cond:
                with_reduced_f32_disabled(kwargs["self"], lambda: f(**kwargs))
                if bf32_cond:
                    with_bf32_enabled(kwargs["self"], lambda: f(**kwargs))
                if tf32_cond:
                    with_tf32_enabled(kwargs["self"], lambda: f(**kwargs))
            else:
                f(**kwargs)