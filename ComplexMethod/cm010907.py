def __init__(
        self,
        optimizer: Optimizer,
        base_lr: float | list[float],
        max_lr: float | list[float],
        step_size_up: int = 2000,
        step_size_down: int | None = None,
        mode: Literal["triangular", "triangular2", "exp_range"] = "triangular",
        gamma: float = 1.0,
        scale_fn: Callable[[float], float] | None = None,
        scale_mode: Literal["cycle", "iterations"] = "cycle",
        cycle_momentum: bool = True,
        base_momentum: float = 0.8,
        max_momentum: float = 0.9,
        last_epoch: int = -1,
    ) -> None:
        # Attach optimizer
        if not isinstance(optimizer, Optimizer):
            raise TypeError(f"{type(optimizer).__name__} is not an Optimizer")
        self.optimizer = optimizer

        base_lrs = _format_param("base_lr", optimizer, base_lr)
        if last_epoch == -1:
            for lr, group in zip(base_lrs, optimizer.param_groups, strict=True):
                _update_param_group_val(group, "lr", lr)

        self.max_lrs = _format_param("max_lr", optimizer, max_lr)

        # pyrefly: ignore [bad-assignment]
        step_size_up = float(step_size_up)
        step_size_down = (
            # pyrefly: ignore [bad-assignment]
            float(step_size_down) if step_size_down is not None else step_size_up
        )
        # pyrefly: ignore [unsupported-operation]
        self.total_size = step_size_up + step_size_down
        self.step_ratio = step_size_up / self.total_size

        if mode not in ["triangular", "triangular2", "exp_range"] and scale_fn is None:
            raise ValueError("mode is invalid and scale_fn is None")

        self.mode = mode
        self.gamma = gamma

        self._scale_fn_ref: Callable[[float], float]
        self._scale_fn_custom = scale_fn
        self.scale_mode = scale_mode
        self._init_scale_fn()

        self.cycle_momentum = cycle_momentum
        if cycle_momentum:
            if (
                "momentum" not in optimizer.defaults
                and "betas" not in optimizer.defaults
            ):
                raise ValueError(
                    "optimizer must support momentum or beta1 with `cycle_momentum` option enabled"
                )

            self.use_beta1 = "betas" in self.optimizer.defaults
            self.base_momentums = _format_param(
                "base_momentum", optimizer, base_momentum
            )
            self.max_momentums = _format_param("max_momentum", optimizer, max_momentum)
            if last_epoch == -1:
                for m_momentum, b_momentum, group in zip(
                    self.max_momentums,
                    self.base_momentums,
                    optimizer.param_groups,
                    strict=True,
                ):
                    if self.use_beta1:
                        group["betas"] = (m_momentum, *group["betas"][1:])
                    else:
                        group["momentum"] = m_momentum
                    group["max_momentum"] = m_momentum
                    group["base_momentum"] = b_momentum

        super().__init__(optimizer, last_epoch)
        self.base_lrs = base_lrs