def __init__(
        self,
        params: ParamsT,
        lr: float | Tensor = 2e-3,
        betas: tuple[float, float] = (0.9, 0.999),
        eps: float = 1e-8,
        weight_decay: float = 0,
        momentum_decay: float = 4e-3,
        decoupled_weight_decay: bool = False,
        *,
        foreach: bool | None = None,
        maximize: bool = False,
        capturable: bool = False,
        differentiable: bool = False,
    ) -> None:
        if isinstance(lr, Tensor) and lr.numel() != 1:
            raise ValueError("Tensor lr must be 1-element")
        if not 0.0 <= lr:
            raise ValueError(f"Invalid learning rate: {lr}")
        if not 0.0 <= eps:
            raise ValueError(f"Invalid epsilon value: {eps}")
        if not 0.0 <= betas[0] < 1.0:
            raise ValueError(f"Invalid beta parameter at index 0: {betas[0]}")
        if not 0.0 <= betas[1] < 1.0:
            raise ValueError(f"Invalid beta parameter at index 1: {betas[1]}")
        if not 0.0 <= weight_decay:
            raise ValueError(f"Invalid weight_decay value: {weight_decay}")
        if not 0.0 <= momentum_decay:
            raise ValueError(f"Invalid momentum_decay value: {momentum_decay}")
        defaults = {
            "lr": lr,
            "betas": betas,
            "eps": eps,
            "weight_decay": weight_decay,
            "momentum_decay": momentum_decay,
            "decoupled_weight_decay": decoupled_weight_decay,
            "maximize": maximize,
            "foreach": foreach,
            "capturable": capturable,
            "differentiable": differentiable,
        }
        super().__init__(params, defaults)