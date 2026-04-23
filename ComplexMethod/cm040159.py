def __init__(
        self,
        inner_optimizer,
        initial_scale=2.0**15,
        dynamic_growth_steps=2000,
        name=None,
        **kwargs,
    ):
        if not kwargs.pop("dynamic", True):
            raise ValueError(
                "LossScaleOptimizer no longer supports `dynamic=False`. "
                "Instead, simply set `loss_scale_factor` directly on the "
                "`inner_optimizer`."
            )

        # Backwards compatibility code for deserialization.
        # LossScaleOptimizer used to return all these parameters in `get_config`
        # from `super.get_config` even though they are all non-functional. We
        # no longer let user set them, but we have to allow the default values
        # to be passed during deserialization to support older models.
        base_optimizer_defaults = {
            "weight_decay": None,
            "clipnorm": None,
            "global_clipnorm": None,
            "clipvalue": None,
            "use_ema": False,
            "ema_momentum": 0.99,
            "ema_overwrite_frequency": None,
            "loss_scale_factor": None,
            "gradient_accumulation_steps": None,
        }
        for arg_name, default_value in base_optimizer_defaults.items():
            if arg_name not in kwargs:
                continue
            arg_value = kwargs.pop(arg_name)
            if (
                default_value is None and arg_value is not None
            ) or arg_value != default_value:
                raise ValueError(
                    f"LossScaleOptimizer does not support `{arg_name}`. "
                    f"Instead, set `{arg_name}` on the `inner_optimizer`."
                )

        if kwargs:
            raise ValueError(
                "LossScaleOptimizer does not support arguments: "
                f"`{'`, `'.join(kwargs.keys())}`."
            )

        super().__init__(learning_rate=0.0, name=name)
        self.inner_optimizer = inner_optimizer
        self.initial_scale = initial_scale
        self.dynamic_growth_steps = dynamic_growth_steps
        # Disable the inner optimizer's loss scaling, otherwise
        # gradients will be scaled twice.
        self.inner_optimizer.loss_scale_factor = None