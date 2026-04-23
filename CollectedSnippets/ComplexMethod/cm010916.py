def __init__(
        self,
        params: ParamsT,
        lr: float | Tensor = 1e-2,
        lr_decay: float = 0,
        weight_decay: float = 0,
        initial_accumulator_value: float = 0,
        eps: float = 1e-10,
        foreach: bool | None = None,
        *,
        maximize: bool = False,
        differentiable: bool = False,
        fused: bool | None = None,
    ) -> None:
        if isinstance(lr, Tensor) and lr.numel() != 1:
            raise ValueError("Tensor lr must be 1-element")
        if not 0.0 <= lr:
            raise ValueError(f"Invalid learning rate: {lr}")
        if not 0.0 <= lr_decay:
            raise ValueError(f"Invalid lr_decay value: {lr_decay}")
        if not 0.0 <= weight_decay:
            raise ValueError(f"Invalid weight_decay value: {weight_decay}")
        if not 0.0 <= initial_accumulator_value:
            raise ValueError(
                f"Invalid initial_accumulator_value value: {initial_accumulator_value}"
            )
        if not 0.0 <= eps:
            raise ValueError(f"Invalid epsilon value: {eps}")

        defaults = {
            "lr": lr,
            "lr_decay": lr_decay,
            "eps": eps,
            "weight_decay": weight_decay,
            "initial_accumulator_value": initial_accumulator_value,
            "foreach": foreach,
            "maximize": maximize,
            "differentiable": differentiable,
            "fused": fused,
        }
        super().__init__(params, defaults)

        if fused:
            if differentiable:
                raise RuntimeError("`fused` does not support `differentiable`")
            if foreach:
                raise RuntimeError("`fused` and `foreach` cannot be `True` together.")
            self._need_device_dtype_check_for_fused = True
            self._step_supports_amp_scaling = True

        for group in self.param_groups:
            for p in group["params"]:
                state = self.state[p]
                state["step"] = (
                    torch.zeros(
                        (),
                        dtype=_get_scalar_dtype(is_fused=group["fused"]),
                        device=p.device,
                    )
                    if group["fused"]
                    else torch.tensor(0.0, dtype=_get_scalar_dtype())
                )
                init_value = (
                    complex(initial_accumulator_value, initial_accumulator_value)
                    if torch.is_complex(p)
                    else initial_accumulator_value
                )
                state["sum"] = torch.full_like(
                    p, init_value, memory_format=torch.preserve_format
                )