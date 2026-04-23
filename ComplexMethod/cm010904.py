def __init__(
        self,
        params: ParamsT,
        lr: float | Tensor = 1e-3,
        momentum: float = 0,
        dampening: float = 0,
        weight_decay: float | Tensor = 0,
        nesterov: bool = False,
        *,
        maximize: bool = False,
        foreach: bool | None = None,
        differentiable: bool = False,
        fused: bool | None = None,
    ) -> None:
        if isinstance(lr, Tensor) and lr.numel() != 1:
            raise ValueError("Tensor lr must be 1-element")
        if lr < 0.0:
            raise ValueError(f"Invalid learning rate: {lr}")
        if momentum < 0.0:
            raise ValueError(f"Invalid momentum value: {momentum}")
        if weight_decay < 0.0:
            raise ValueError(f"Invalid weight_decay value: {weight_decay}")

        defaults = {
            "lr": lr,
            "momentum": momentum,
            "dampening": dampening,
            "weight_decay": weight_decay,
            "nesterov": nesterov,
            "maximize": maximize,
            "foreach": foreach,
            "differentiable": differentiable,
            "fused": fused,
        }
        if nesterov and (momentum <= 0 or dampening != 0):
            raise ValueError("Nesterov momentum requires a momentum and zero dampening")
        super().__init__(params, defaults)

        if fused:
            self._step_supports_amp_scaling = True
            self._need_device_dtype_check_for_fused = True
            if differentiable:
                raise RuntimeError("`fused` does not support `differentiable`")
            if foreach:
                raise RuntimeError("`fused` and `foreach` cannot be `True` together.")